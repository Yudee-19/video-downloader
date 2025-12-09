import asyncio
import logging
import yt_dlp
import urllib.parse
from config import COOKIES_FILE

logger = logging.getLogger(__name__)

class MyYtLogger:
    """Silences yt-dlp spam so logs stay clean"""
    def debug(self, msg): pass
    def warning(self, msg): logger.warning(f"[yt-dlp] {msg}")
    def error(self, msg): logger.error(f"[yt-dlp] {msg}")

async def get_stream_url(youtube_url: str):
    """
    Step 1: Get the 'Golden Link' AND the 'Headers' needed to access it.
    """
    ydl_opts = {
        'cookiefile': COOKIES_FILE,
        'format': 'best[height=1080][protocol^=m3u8]/bestvideo[height=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'logger': MyYtLogger(),
    }

    loop = asyncio.get_event_loop()
    # Run blocking extraction in a thread
    info = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(youtube_url, download=False))
    
    url_list = []
    
    if 'requested_formats' in info:
        url_list = [f['url'] for f in info['requested_formats']]
        
    elif 'url' in info:
        url_list = [info['url']]
    else:
        raise Exception("No stream URL found")

    # must pass the User-Agent to FFmpeg, or YouTube gives 403 Forbidden.
    headers = info.get('http_headers', {})
    user_agent = headers.get('User-Agent', 'Mozilla/5.0')

    title = info.get('title', 'video')
    return url_list, title, user_agent

async def generate_stream(url_list, user_agent):
    """
    Step 2: The Zero-CPU Pipeline with Headers.
    """
    ffmpeg_cmd = [
        'ffmpeg',
        '-reconnect', '1', 
        '-reconnect_streamed', '1', 
        '-reconnect_delay_max', '5',
        '-loglevel', 'error',
        # PASS THE ID CARD (User-Agent)
        '-user_agent', user_agent
    ]

    for stream_url in url_list:
        ffmpeg_cmd.extend(['-i', stream_url])

    if len(url_list) > 1:
        ffmpeg_cmd.extend(['-map', '0:v', '-map', '1:a'])

    ffmpeg_cmd.extend([
        '-c', 'copy',           # Zero CPU
        '-f', 'mp4',            # Container
        '-movflags', 'frag_keyframe+empty_moov', # Streamable
        '-'                     # Output to Pipe
    ])

    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE # Capture errors for debugging
    )

    try:
        while True:
            chunk = await process.stdout.read(32 * 1024)
            if not chunk:
                # If EOF but process failed, log it
                if process.returncode is not None and process.returncode != 0:
                    error_log = await process.stderr.read()
                    logger.error(f"FFmpeg Error: {error_log.decode()}")
                break
            yield chunk
    except Exception:
        if process.returncode is None:
            try:
                process.kill()
            except:
                pass
    finally:
        if process.returncode is None:
            try:
                process.kill()
            except:
                pass