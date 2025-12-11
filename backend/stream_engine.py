# import asyncio
# import yt_dlp
# from fastapi import HTTPException
# from config import COOKIES_FILE, logger
# from core import MyYtLogger

# async def extract_stream_info(url: str):
#     """
#     Extracts the best video and audio stream URLs using yt-dlp.
#     Logic is DITTO Uday's original implementation.
#     """
#     logger.info(f"--- NEW HIGH-SCALE REQUEST: {url} ---")

#     ydl_opts = {
#         'cookiefile': COOKIES_FILE,
#         # Exact format string from original code
#         'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
#         'quiet': True,
#         'logger': MyYtLogger(logger),
#     }

#     try:
#         # Run blocking yt-dlp code in a thread to keep async loop free
#         loop = asyncio.get_event_loop()
#         info = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=False))

#         url_list = []
#         if 'requested_formats' in info:
#             url_list = [f['url'] for f in info['requested_formats']]
#         elif 'url' in info:
#             url_list = [info['url']]
#         else:
#             raise HTTPException(status_code=500, detail="No stream URLs found")

#         title = info.get('title', 'video').replace('"', '').replace("'", "")
#         return url_list, title

#     except Exception as e:
#         logger.error(f"Extraction failed: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# async def generate_stream_chunks(url_list: list):
#     """
#     Generates video chunks via FFmpeg copy (Zero-CPU).
#     Logic is DITTO Uday's original implementation.
#     """
#     ffmpeg_cmd = [
#         'ffmpeg',
#         '-reconnect', '1',
#         '-reconnect_streamed', '1',
#         '-reconnect_delay_max', '5',
#         '-loglevel', 'error'
#     ]

#     for stream_url in url_list:
#         ffmpeg_cmd.extend(['-i', stream_url])

#     if len(url_list) > 1:
#         ffmpeg_cmd.extend(['-map', '0:v', '-map', '1:a'])

#     ffmpeg_cmd.extend([
#         '-c', 'copy',
#         '-f', 'mp4',
#         '-movflags', 'frag_keyframe+empty_moov',
#         '-'
#     ])

#     process = await asyncio.create_subprocess_exec(
#         *ffmpeg_cmd,
#         stdout=asyncio.subprocess.PIPE,
#         stderr=asyncio.subprocess.DEVNULL
#     )

#     try:
#         while True:
#             # exact buffer size from original (32KB)
#             chunk = await process.stdout.read(32 * 1024)
#             if not chunk:
#                 break
#             yield chunk
#     except Exception as e:
#         logger.error(f"Stream broken: {e}")
#     finally:
#         if process.returncode is None:
#             try:
#                 process.kill()
#             except ProcessLookupError:
#                 pass
#         logger.info("Async stream closed.")

import asyncio
import yt_dlp
from fastapi import HTTPException
from config import COOKIES_FILE, logger, USER_AGENTS
from core import MyYtLogger

async def extract_stream_info(url: str):
    """
    Extracts stream URLs AND the HTTP headers needed to access them.
    """
    logger.info(f"--- NEW HIGH-SCALE REQUEST: {url} ---")
    print(f"Using cookies file: {COOKIES_FILE}")
    ydl_opts = {
        'force_ipv4': True,  # Fix: Force IPv4 as IPv6 often gets 403 throttled on AWS/Docker
        'cookiefile': COOKIES_FILE,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'logger': MyYtLogger(logger),
        # Fix: Force IPv4 as IPv6 often gets 403 throttled on AWS/Docker
        # 'source_address': '0.0.0.0', 
        'remote_components': ['ejs:github'],

    }

    try:
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
        
        # CRITICAL: Extract the headers yt-dlp generated (Cookies, User-Agent, etc.)
        # We need these to pass to FFmpeg, otherwise 403 Forbidden.
        yt_headers = {}

        # 1) If global headers exist, use them
        if "http_headers" in info and info["http_headers"]:
            yt_headers = info["http_headers"]

        # 2) Otherwise check requested_formats
        if not yt_headers and "requested_formats" in info:
            for fmt in info["requested_formats"]:
                if "http_headers" in fmt and fmt["http_headers"]:
                    yt_headers = fmt["http_headers"]
                    break

        # 3) Otherwise check formats list
        if not yt_headers and "formats" in info:
            for fmt in info["formats"]:
                if "http_headers" in fmt and fmt["http_headers"]:
                    yt_headers = fmt["http_headers"]
                    break

        print("FINAL HEADERS SELECTED:", yt_headers)

        print("Extracted yt-dlp headers:", yt_headers)
        return url_list, title, yt_headers

    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def generate_stream_chunks(url_list: list, headers: dict):
    """
    Generates video chunks via FFmpeg, injecting the correct headers.
    """

    print("Generating stream with headers:", headers)
    # Convert HTTP headers to ffmpeg format once
    header_args = "\r\n".join([f"{k}: {v}" for k, v in headers.items()])


    print("FFMPEG HEADERS:", header_args)
    ffmpeg_cmd = [
        'ffmpeg',
        '-reconnect', '1',
        '-reconnect_streamed', '1',
        '-reconnect_delay_max', '5',
        '-loglevel', 'error',
        '-headers', header_args,   # APPLY HEADERS BEFORE ALL INPUTS
    ]

    # Add each input
    for stream_url in url_list:
        ffmpeg_cmd.extend(['-i', stream_url])

    # Map video + audio
    if len(url_list) > 1:
        ffmpeg_cmd.extend(['-map', '0:v:0', '-map', '1:a:0'])

    ffmpeg_cmd.extend([
        '-c:v', 'copy',
        '-c:a', 'copy',
        '-f', 'mp4',
        '-movflags', 'frag_keyframe+empty_moov',
        'pipe:1'
    ])

    # Debug print
    print("FINAL FFMPEG CMD:", ffmpeg_cmd)

    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    try:
        while True:
            chunk = await process.stdout.read(32 * 1024)
            if not chunk:
                break
            yield chunk
    except Exception as e:
        logger.error(f"Stream broken: {e}")
    finally:
        if process.returncode is None:
            process.kill()
        logger.info("Async stream closed.")
   

