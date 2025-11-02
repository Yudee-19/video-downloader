from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import os
import uuid
from typing import Optional
import subprocess
import random

app = FastAPI(title="YouTube & Instagram Downloader API")

# Get CORS origins from environment variable or use default
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

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

# Cookies file path - works for both local and Docker
COOKIES_FILE = os.getenv("COOKIES_FILE", "/app/cookies.txt" if os.path.exists("/app/cookies.txt") else "cookies.txt")

class DownloadRequest(BaseModel):
    url: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    audio_only: Optional[bool] = False

class DownloadResponse(BaseModel):
    file_id: str
    message: str

class StatusResponse(BaseModel):
    ready: bool
    filename: Optional[str] = None
    error: Optional[str] = None

# Store download status
download_status = {}

# List of User-Agent strings for randomization (helps avoid bot detection)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:118.0) Gecko/20100101 Firefox/118.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

def download_video_task(file_id: str, url: str, start_time: Optional[str], end_time: Optional[str], audio_only: bool):
    """Background task to download video using yt-dlp"""
    try:
        filepath = f"{TEMP_DIR}/{file_id}"
        
        # Randomize User-Agent to avoid bot detection
        selected_user_agent = random.choice(USER_AGENTS)
        
        # Base options for all downloads
        base_opts = {
            'outtmpl': f'{filepath}.%(ext)s',
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
            output_file = f"{filepath}_trimmed.mp4"
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
        
        download_status[file_id] = {
            "ready": True,
            "filename": os.path.basename(filename),
            "filepath": filename,
            "error": None
        }
    
    except Exception as e:
        download_status[file_id] = {
            "ready": False,
            "filename": None,
            "filepath": None,
            "error": str(e)
        }

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
    download_status[video_id] = {
        "ready": False,
        "filename": None,
        "filepath": None,
        "error": None
    }
    
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

@app.get("/status/{file_id}", response_model=StatusResponse)
async def check_status(file_id: str):
    """
    Check download status
    """
    if file_id not in download_status:
        raise HTTPException(status_code=404, detail="File ID not found")
    
    status = download_status[file_id]
    return StatusResponse(
        ready=status["ready"],
        filename=status["filename"],
        error=status["error"]
    )

@app.get("/video/{file_id}")
async def get_video(file_id: str):
    """
    Serve the downloaded video file
    """
    if file_id not in download_status:
        raise HTTPException(status_code=404, detail="File ID not found")
    
    status = download_status[file_id]
    
    if not status["ready"]:
        raise HTTPException(status_code=400, detail="File not ready yet")
    
    if status["error"]:
        raise HTTPException(status_code=500, detail=status["error"])
    
    filepath = status["filepath"]
    
    if not os.path.exists(filepath):
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
    if file_id in download_status:
        status = download_status[file_id]
        if status["filepath"] and os.path.exists(status["filepath"]):
            os.remove(status["filepath"])
        del download_status[file_id]
        return {"message": "File cleaned up successfully"}
    
    raise HTTPException(status_code=404, detail="File ID not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
