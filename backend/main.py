from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import os
import uuid
from typing import Optional, List
import subprocess
import random
import redis
import json
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
import shlex
import logging
import sys
import yt_dlp
print(f"🚀 Loaded yt-dlp version: {yt_dlp.version.__version__}")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        # ADD encoding='utf-8' HERE:
        logging.FileHandler("stream_log.log", encoding='utf-8'), 
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI(title="YouTube & Instagram Downloader API")

# Get CORS origins from environment variable or use default
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Initialize Redis connection
redis_client = None
try:
    redis_config = {
        'host': REDIS_HOST,
        'port': REDIS_PORT,
        'decode_responses': True,
        'socket_connect_timeout': 5,
        'socket_timeout': 5,
        'retry_on_timeout': True
    }
    if REDIS_PASSWORD:
        redis_config['password'] = REDIS_PASSWORD
    
    redis_client = redis.Redis(**redis_config)
    redis_client.ping()
    print(f"✅ Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    print(f"⚠️  Redis connection failed: {e}")
    print("⚠️  Falling back to in-memory storage (not recommended for production)")
    redis_client = None

# Thread pool for parallel downloads
MAX_PARALLEL_DOWNLOADS = int(os.getenv("MAX_PARALLEL_DOWNLOADS", "3"))
executor = ThreadPoolExecutor(max_workers=MAX_PARALLEL_DOWNLOADS)

# Lock for thread-safe operations
download_lock = threading.Lock()

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins= ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get temp directory from environment or use default
TEMP_DIR = os.getenv("TEMP_DIR", "tmp_videos")
os.makedirs(TEMP_DIR, exist_ok=True)

# ... imports ...

# UPDATE THIS BLOCK
# Check Render's secret path first, then fall back to local for development
if os.path.exists("/etc/secrets/cookies.txt"):
    COOKIES_FILE = "/etc/secrets/cookies.txt"
else:
    COOKIES_FILE = "cookies.txt"  # For local testing

# Cookies file path - works for both local and Docker
# COOKIES_FILE = os.getenv("COOKIES_FILE", "/app/cookies.txt" if os.path.exists("/app/cookies.txt") else "cookies.txt")

class DownloadRequest(BaseModel):
    url: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    audio_only: Optional[bool] = False

class BatchItem(BaseModel):
    url: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None

class BatchDownloadRequest(BaseModel):
    # New preferred schema: per-item timestamps
    items: Optional[List[BatchItem]] = None
    # Backward compatibility: original schema
    urls: Optional[List[str]] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    audio_only: Optional[bool] = False

class DownloadResponse(BaseModel):
    file_id: str
    message: str

class BatchDownloadResponse(BaseModel):
    batch_id: str
    download_ids: List[str]
    message: str

class StatusResponse(BaseModel):
    ready: bool
    filename: Optional[str] = None
    error: Optional[str] = None
    progress: Optional[str] = None
    status: Optional[str] = None

class BatchStatusResponse(BaseModel):
    batch_id: str
    total: int
    completed: int
    failed: int
    in_progress: int
    downloads: List[dict]


class MyYtLogger:
    def __init__(self, app_logger):
        self.logger = app_logger

    def debug(self, msg):
        # Redirect yt-dlp debug messages to logger.info so they show up in your log file
        # We filter out the specific "read 1024 bytes" noise if desired, or keep it all.
        if not msg.startswith('[debug] '): 
            # Optionally add a prefix to make it clear it's from yt-dlp
            self.logger.info(f"[yt-dlp] {msg}")
        else:
            self.logger.info(f"{msg}")

    def warning(self, msg):
        self.logger.warning(f"[yt-dlp] {msg}")

    def error(self, msg):
        self.logger.error(f"[yt-dlp] {msg}")
# Store download status (fallback for when Redis is not available)
download_status = {}

# Redis key prefixes
REDIS_DOWNLOAD_KEY = "download:"
REDIS_BATCH_KEY = "batch:"
REDIS_QUEUE_KEY = "queue:downloads"

# List of User-Agent strings for randomization (helps avoid bot detection)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:118.0) Gecko/20100101 Firefox/118.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Helper functions for Redis storage
def set_download_status(file_id: str, status: dict):
    """Set download status in Redis or fallback to memory"""
    if redis_client:
        try:
            redis_client.setex(
                f"{REDIS_DOWNLOAD_KEY}{file_id}",
                3600,  # Expire after 1 hour
                json.dumps(status)
            )
        except Exception as e:
            print(f"Redis error: {e}")
            download_status[file_id] = status
    else:
        download_status[file_id] = status

def get_download_status(file_id: str):
    """Get download status from Redis or fallback to memory"""
    if redis_client:
        try:
            data = redis_client.get(f"{REDIS_DOWNLOAD_KEY}{file_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Redis error: {e}")
            return download_status.get(file_id)
    else:
        return download_status.get(file_id)

def delete_download_status(file_id: str):
    """Delete download status from Redis or memory"""
    if redis_client:
        try:
            redis_client.delete(f"{REDIS_DOWNLOAD_KEY}{file_id}")
        except Exception as e:
            print(f"Redis error: {e}")
            if file_id in download_status:
                del download_status[file_id]
    else:
        if file_id in download_status:
            del download_status[file_id]

def set_batch_status(batch_id: str, status: dict):
    """Set batch status in Redis or fallback to memory"""
    if redis_client:
        try:
            redis_client.setex(
                f"{REDIS_BATCH_KEY}{batch_id}",
                3600,  # Expire after 1 hour
                json.dumps(status)
            )
        except Exception as e:
            print(f"Redis error: {e}")
            download_status[f"batch_{batch_id}"] = status
    else:
        download_status[f"batch_{batch_id}"] = status

def get_batch_status(batch_id: str):
    """Get batch status from Redis or fallback to memory"""
    if redis_client:
        try:
            data = redis_client.get(f"{REDIS_BATCH_KEY}{batch_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Redis error: {e}")
            return download_status.get(f"batch_{batch_id}")
    else:
        return download_status.get(f"batch_{batch_id}")

def download_video_task(file_id: str, url: str, start_time: Optional[str], end_time: Optional[str], audio_only: bool):
    """Background task to download video using yt-dlp"""
    try:
        # Update status to downloading
        set_download_status(file_id, {
            "ready": False,
            "filename": None,
            "filepath": None,
            "error": None,
            "progress": "0%",
            "status": "downloading"
        })
        
        # Randomize User-Agent to avoid bot detection
        selected_user_agent = random.choice(USER_AGENTS)
        
        # Base options for all downloads
        base_opts = {
            'outtmpl': f'{TEMP_DIR}/%(title)s.%(ext)s',  # Use video title as filename
            'cookiefile': COOKIES_FILE,         # ✅ Use cookies to bypass bot detection
            'http_headers': {                   # ✅ Randomized headers
                'User-Agent': selected_user_agent,
                'Accept-Language': 'en-US,en;q=0.9',
            },
            'retries': 5,
            'fragment_retries': 5,
        }
        
        if audio_only:
            # Download audio only
            ydl_opts = {
                **base_opts,
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'postprocessor_args': [
                    '-ar', '44100',  # Set audio sample rate
                ],
                'prefer_ffmpeg': True,
            }
        else:
            # Download video
            ydl_opts = {
                **base_opts,
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
            }
        
        # Download the video/audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # For audio only, the file extension changes to .mp3 after post-processing
            if audio_only:
                # Replace the original extension with .mp3
                base_filename = os.path.splitext(filename)[0]
                filename = f"{base_filename}.mp3"
        
        # If trimming is needed and ffmpeg is available
        if (start_time or end_time) and not audio_only:
            set_download_status(file_id, {
                "ready": False,
                "filename": None,
                "filepath": None,
                "error": None,
                "progress": "90%",
                "status": "trimming"
            })
            
            # Extract base filename without extension for trimmed output
            base_filename = os.path.splitext(filename)[0]
            output_file = f"{base_filename}_trimmed.mp4"
            cmd = ['ffmpeg', '-i', filename]
            
            if start_time:
                cmd.extend(['-ss', start_time])
            if end_time:
                cmd.extend(['-to', end_time])
            
            cmd.extend(['-c', 'copy', output_file])
            
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                os.remove(filename)  # Remove original
                filename = output_file
            except Exception as e:
                print(f"Trimming failed: {e}")
                # Continue with original file
        
        set_download_status(file_id, {
            "ready": True,
            "filename": os.path.basename(filename),
            "filepath": filename,
            "error": None,
            "progress": "100%",
            "status": "completed"
        })
    
    except Exception as e:
        set_download_status(file_id, {
            "ready": False,
            "filename": None,
            "filepath": None,
            "error": str(e),
            "progress": "0%",
            "status": "failed"
        })


@app.get("/stream-download")
async def stream_download(url: str):
    logger.info(f"--- NEW HIGH-SCALE REQUEST: {url} ---")

    # 1. OPTIMIZED FORMAT SELECTION
    # We specifically request MP4 video and M4A audio. 
    # This ensures both are compatible with the MP4 container WITHOUT transcoding.
    ydl_opts = {
        'cookiefile': COOKIES_FILE,  # <--- This must use the variable we defined above
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'logger': MyYtLogger(logger),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            url_list = []
            
            # Logic to extract separate streams if available
            if 'requested_formats' in info:
                url_list = [f['url'] for f in info['requested_formats']]
            elif 'url' in info:
                url_list = [info['url']]
            else:
                raise HTTPException(status_code=500, detail="No stream URLs found")

            title = info.get('title', 'video').replace('"', '').replace("'", "")
            
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # 2. OPTIMIZED FFMPEG COMMAND (ZERO-CPU COPY)
    # Note: We use '-c copy' for EVERYTHING. No re-encoding.
    ffmpeg_cmd = [
        'ffmpeg',
        '-reconnect', '1', 
        '-reconnect_streamed', '1', 
        '-reconnect_delay_max', '5',
        '-loglevel', 'error' # Reduce log spam for performance
    ]

    # Add all inputs
    for stream_url in url_list:
        ffmpeg_cmd.extend(['-i', stream_url])

    # Map streams if we have multiple (usually video + audio)
    if len(url_list) > 1:
        ffmpeg_cmd.extend(['-map', '0:v', '-map', '1:a'])

    ffmpeg_cmd.extend([
        '-c', 'copy',          # <--- THE MAGIC KEY: 0% CPU Usage
        '-f', 'mp4', 
        '-movflags', 'frag_keyframe+empty_moov', 
        '-'
    ])

    # 3. ASYNC PROCESS MANAGEMENT (Non-Blocking)
    # This allows Python to handle 100+ connections without 100+ threads
    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )

    async def async_generator():
        try:
            while True:
                # Await the read so the loop can handle other users while waiting for data
                chunk = await process.stdout.read(32 * 1024) # 32KB chunks
                if not chunk:
                    break
                yield chunk
        except Exception as e:
            logger.error(f"Stream broken: {e}")
        finally:
            if process.returncode is None:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
            logger.info("Async stream closed.")

    return StreamingResponse(
        async_generator(),
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
        "supported_platforms": ["YouTube", "Instagram"]
    }

@app.post("/download", response_model=DownloadResponse)
async def download_video(request: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Initiate video download from YouTube or Instagram
    Supports:
    - YouTube videos (youtube.com, youtu.be)
    - Instagram reels and videos (instagram.com)
    """
    video_id = str(uuid.uuid4())
    
    # Initialize status
    set_download_status(video_id, {
        "ready": False,
        "filename": None,
        "filepath": None,
        "error": None,
        "progress": "0%",
        "status": "queued"
    })
    
    # Add download task to background
    background_tasks.add_task(
        download_video_task,
        video_id,
        request.url,
        request.start_time,
        request.end_time,
        request.audio_only
    )
    
    return DownloadResponse(
        file_id=video_id,
        message="Download started"
    )

@app.post("/batch-download", response_model=BatchDownloadResponse)
async def batch_download(request: BatchDownloadRequest):
    """
    Initiate multiple video downloads in parallel
    Returns a batch ID to track all downloads together
    """
    batch_id = str(uuid.uuid4())
    download_ids = []

    # Normalize input into a list of (url, start, end)
    tasks: List[tuple] = []
    if request.items and len(request.items) > 0:
        for it in request.items:
            tasks.append((it.url, it.start_time, it.end_time))
    elif request.urls and len(request.urls) > 0:
        # Backward compatibility: apply the same timestamps to all URLs
        for url in request.urls:
            tasks.append((url, request.start_time, request.end_time))
    else:
        raise HTTPException(status_code=400, detail="No items or urls provided for batch download")

    # Create individual download tasks
    for url, start_t, end_t in tasks:
        video_id = str(uuid.uuid4())
        download_ids.append(video_id)

        # Initialize status
        set_download_status(video_id, {
            "ready": False,
            "filename": None,
            "filepath": None,
            "error": None,
            "progress": "0%",
            "status": "queued",
            "url": url,
            "batch_id": batch_id,
            "start_time": start_t,
            "end_time": end_t,
        })

        # Submit to thread pool for parallel execution
        executor.submit(
            download_video_task,
            video_id,
            url,
            start_t,
            end_t,
            request.audio_only
        )
    
    # Store batch metadata
    set_batch_status(batch_id, {
        "batch_id": batch_id,
        "download_ids": download_ids,
        "created_at": datetime.now().isoformat(),
        "total": len(download_ids)
    })
    
    return BatchDownloadResponse(
        batch_id=batch_id,
        download_ids=download_ids,
        message=f"Started batch download of {len(download_ids)} videos"
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
        status=status.get("status", "unknown")
    )

@app.get("/batch-status/{batch_id}", response_model=BatchStatusResponse)
async def check_batch_status(batch_id: str):
    """
    Check status of all downloads in a batch
    """
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
            downloads.append({
                "file_id": download_id,
                "url": status.get("url", ""),
                "start_time": status.get("start_time"),
                "end_time": status.get("end_time"),
                "status": status.get("status", "unknown"),
                "progress": status.get("progress", "0%"),
                "filename": status.get("filename"),
                "error": status.get("error"),
                "ready": status.get("ready", False)
            })
            
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
        downloads=downloads
    )

@app.get("/video/{file_id}")
async def get_video(file_id: str):
    """
    Serve the downloaded video file
    """
    status = get_download_status(file_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="File ID not found")
    
    if not status.get("ready"):
        raise HTTPException(status_code=400, detail="File not ready yet")
    
    if status.get("error"):
        raise HTTPException(status_code=500, detail=status["error"])
    
    filepath = status.get("filepath")
    
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found on server")
    
    return FileResponse(
        filepath,
        filename=status["filename"],
        media_type='application/octet-stream'
    )

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
                    print(f"Failed to delete {filepath}: {e}")
            delete_download_status(download_id)
    
    # Clean up batch metadata
    if redis_client:
        try:
            redis_client.delete(f"{REDIS_BATCH_KEY}{batch_id}")
        except Exception as e:
            print(f"Redis error: {e}")
    
    return {"message": f"Cleaned up {cleaned} files from batch"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
