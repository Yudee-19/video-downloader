import asyncio
import yt_dlp
from fastapi import HTTPException
from config import COOKIES_FILE, logger
from core import MyYtLogger

async def extract_stream_info(url: str):
    """
    Extracts the best video and audio stream URLs using yt-dlp.
    Logic is DITTO Uday's original implementation.
    """
    logger.info(f"--- NEW HIGH-SCALE REQUEST: {url} ---")

    ydl_opts = {
        'cookiefile': COOKIES_FILE,
        # Exact format string from original code
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'logger': MyYtLogger(logger),
    }

    try:
        # Run blocking yt-dlp code in a thread to keep async loop free
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=False))
        
        url_list = []
        if 'requested_formats' in info:
            url_list = [f['url'] for f in info['requested_formats']]
        elif 'url' in info:
            url_list = [info['url']]
        else:
            raise HTTPException(status_code=500, detail="No stream URLs found")

        title = info.get('title', 'video').replace('"', '').replace("'", "")
        return url_list, title

    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def generate_stream_chunks(url_list: list):
    """
    Generates video chunks via FFmpeg copy (Zero-CPU).
    Logic is DITTO Uday's original implementation.
    """
    ffmpeg_cmd = [
        'ffmpeg',
        '-reconnect', '1', 
        '-reconnect_streamed', '1', 
        '-reconnect_delay_max', '5',
        '-loglevel', 'error'
    ]

    for stream_url in url_list:
        ffmpeg_cmd.extend(['-i', stream_url])

    if len(url_list) > 1:
        ffmpeg_cmd.extend(['-map', '0:v', '-map', '1:a'])

    ffmpeg_cmd.extend([
        '-c', 'copy',
        '-f', 'mp4', 
        '-movflags', 'frag_keyframe+empty_moov', 
        '-'
    ])

    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )

    try:
        while True:
            # exact buffer size from original (32KB)
            chunk = await process.stdout.read(32 * 1024)
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