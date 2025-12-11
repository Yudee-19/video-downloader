from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import os
from fastapi.responses import RedirectResponse
from datetime import datetime
from rq import Queue

# Import from our modules
from config import redis_client, logger, redis_raw_client
from models import (
    DownloadRequest,
    BatchDownloadRequest,
    DownloadResponse,
    BatchDownloadResponse,
    StatusResponse,
    BatchStatusResponse,
)
from core import (
    set_download_status,
    get_download_status,
    delete_download_status,
    set_batch_status,
    get_batch_status,
    download_video_task,
    process_single_job,
    REDIS_BATCH_KEY,
)

# Import the new stream engine
from stream_engine import extract_stream_info, generate_stream_chunks

app = FastAPI(title="YouTube & Instagram Downloader API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REDIS QUEUE SETUP ---
if not redis_raw_client:
    logger.warning("⚠️ REDIS NOT CONNECTED! Batch downloads will fail.")
    task_queue = None
else:
    # Use RAW client for the Queue
    task_queue = Queue("default", connection=redis_raw_client)
# -------------------------


@app.get("/stream-download")
async def stream_download(url: str):
    # Unpack 3 values now
    url_list, title, headers = await extract_stream_info(url)

    # Pass headers to the generator
    return StreamingResponse(
        generate_stream_chunks(url_list, headers),
        media_type="video/mp4",
        headers={
            "Content-Disposition": f'attachment; filename="{title}.mp4"',
        },
    )


@app.get("/")
async def root():
    return {
        "message": "YouTube & Instagram Downloader API",
        "status": "running",
        "worker_status": "connected" if task_queue else "offline",
        "supported_platforms": ["YouTube", "Instagram"],
    }


@app.post("/download", response_model=DownloadResponse)
async def download_video(request: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Single Download: Still uses local BackgroundTasks (no S3) for quick tests.
    You can switch this to use process_single_job if you want S3 for everything.
    """
    video_id = str(uuid.uuid4())

    set_download_status(
        video_id,
        {
            "ready": False,
            "filename": None,
            "filepath": None,
            "error": None,
            "progress": "0%",
            "status": "queued",
        },
    )

    background_tasks.add_task(
        download_video_task,
        video_id,
        request.url,
        request.start_time,
        request.end_time,
        request.audio_only or False,
    )

    return DownloadResponse(file_id=video_id, message="Download started")


@app.post("/batch-download", response_model=BatchDownloadResponse)
async def batch_download(request: BatchDownloadRequest):
    if not task_queue:
        raise HTTPException(
            status_code=503, detail="Redis Worker is offline. Cannot process batch."
        )

    batch_id = str(uuid.uuid4())
    download_ids = []

    tasks = []
    if request.items and len(request.items) > 0:
        for it in request.items:
            tasks.append((it.url, it.start_time, it.end_time))
    elif request.urls and len(request.urls) > 0:
        for url in request.urls:
            tasks.append((url, request.start_time, request.end_time))
    else:
        raise HTTPException(
            status_code=400, detail="No items or urls provided for batch download"
        )

    for url, start_t, end_t in tasks:
        video_id = str(uuid.uuid4())
        download_ids.append(video_id)

        # 1. Set Initial Status
        set_download_status(
            video_id,
            {
                "ready": False,
                "filename": None,
                "filepath": None,
                "error": None,
                "progress": "0%",
                "status": "queued",
                "url": url,
                "batch_id": batch_id,
            },
        )

        # 2. ENQUEUE THE WRAPPER (Download -> S3 -> Cleanup)
        task_queue.enqueue(
            process_single_job,  # Calls the function in core.py
            args=(video_id, url, start_t, end_t, request.audio_only),
            job_timeout="1h",
        )

    set_batch_status(
        batch_id,
        {
            "batch_id": batch_id,
            "download_ids": download_ids,
            "created_at": datetime.now().isoformat(),
            "total": len(download_ids),
        },
    )

    return BatchDownloadResponse(
        batch_id=batch_id,
        download_ids=download_ids,
        message=f"Queued {len(download_ids)} videos for S3 processing",
    )


@app.get("/status/{file_id}", response_model=StatusResponse)
async def check_status(file_id: str):
    """
    Check download status
    """
    status = get_download_status(file_id)
    if not status:
        raise HTTPException(status_code=404, detail="File ID not found")

    return StatusResponse(
        ready=status.get("ready", False),
        filename=status.get("filename"),
        error=status.get("error"),
        progress=status.get("progress", "0%"),
        status=status.get("status", "unknown"),
        download_url=status.get("download_url"),  # S3 URL for batch downloads
    )


@app.get("/batch-status/{batch_id}", response_model=BatchStatusResponse)
async def check_batch_status(batch_id: str):
    batch = get_batch_status(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch ID not found")

    download_ids = batch.get("download_ids", [])
    downloads = []
    completed = 0
    failed = 0
    in_progress = 0

    for download_id in download_ids:
        status = get_download_status(download_id)
        if status:
            downloads.append(
                {
                    "file_id": download_id,
                    "url": status.get("url", ""),
                    "status": status.get("status", "unknown"),
                    "progress": status.get("progress", "0%"),
                    "filename": status.get("filename"),
                    "download_url": status.get("download_url"),  # S3 Link included here
                    "error": status.get("error"),
                    "ready": status.get("ready", False),
                }
            )

            if status.get("status") == "completed":
                completed += 1
            elif status.get("status") == "failed":
                failed += 1
            elif status.get("status") in ["downloading", "queued", "trimming"]:
                in_progress += 1

    return BatchStatusResponse(
        batch_id=batch_id,
        total=len(download_ids),
        completed=completed,
        failed=failed,
        in_progress=in_progress,
        downloads=downloads,
    )


@app.get("/video/{file_id}")
async def get_video(file_id: str):
    """
    Smart Endpoint:
    - If file is local, serve it.
    - If file is on S3 (Batch), REDIRECT to S3.
    """
    status = get_download_status(file_id)

    if not status:
        raise HTTPException(status_code=404, detail="File ID not found")

    if not status.get("ready"):
        raise HTTPException(status_code=400, detail="File not ready yet")

    if status.get("error"):
        raise HTTPException(status_code=500, detail=status["error"])

    # CHECK 1: Is there an S3 URL? If yes, Redirect!
    # This saves the frontend from needing changes.
    if status.get("download_url"):
        return RedirectResponse(url=status["download_url"])

    # CHECK 2: Is it a local file?
    filepath = status.get("filepath")
    if filepath and os.path.exists(filepath):
        return FileResponse(
            filepath, filename=status["filename"], media_type="application/octet-stream"
        )

    # If neither, we have a problem
    raise HTTPException(status_code=404, detail="File not found (Local or S3)")


@app.delete("/cleanup/{file_id}")
async def cleanup_file(file_id: str):
    """
    Delete downloaded file and clean up status
    """
    status = get_download_status(file_id)

    if status:
        filepath = status.get("filepath")
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        delete_download_status(file_id)
        return {"message": "File cleaned up successfully"}

    raise HTTPException(status_code=404, detail="File ID not found")


@app.delete("/batch-cleanup/{batch_id}")
async def cleanup_batch(batch_id: str):
    """
    Delete all files in a batch and clean up status
    """
    batch = get_batch_status(batch_id)

    if not batch:
        raise HTTPException(status_code=404, detail="Batch ID not found")

    download_ids = batch.get("download_ids", [])
    cleaned = 0

    for download_id in download_ids:
        status = get_download_status(download_id)
        if status:
            filepath = status.get("filepath")
            if filepath and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    cleaned += 1
                except Exception as e:
                    logger.error(f"Failed to delete {filepath}: {e}")
            delete_download_status(download_id)

    # Clean up batch metadata
    if redis_client:
        try:
            redis_client.delete(f"{REDIS_BATCH_KEY}{batch_id}")
        except Exception as e:
            logger.error(f"Redis error: {e}")

    return {"message": f"Cleaned up {cleaned} files from batch"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
