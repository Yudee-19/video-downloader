# import asyncio
# import logging
# import yt_dlp
# import urllib.parse
# import random
# import os
# from config import COOKIES_FILE, USER_AGENTS

# logger = logging.getLogger(__name__)

# class MyYtLogger:
#     def debug(self, msg): pass
#     def warning(self, msg): logger.warning(f"[yt-dlp] {msg}")
#     def error(self, msg): logger.error(f"[yt-dlp] {msg}")

# def parse_cookie_file(cookie_file):
#     """
#     Reads the Netscape cookies.txt and converts it to a header string:
#     'Cookie: key1=value1; key2=value2;'
#     """
#     if not os.path.exists(cookie_file):
#         return ""
    
#     cookies = []
#     try:
#         with open(cookie_file, 'r') as f:
#             for line in f:
#                 if not line.startswith('#') and line.strip():
#                     fields = line.strip().split('\t')
#                     if len(fields) >= 7:
#                         name = fields[5]
#                         value = fields[6]
#                         cookies.append(f"{name}={value}")
#         return "; ".join(cookies)
#     except Exception as e:
#         logger.error(f"Cookie Parse Error: {e}")
#         return ""

# async def get_stream_url(youtube_url: str):
#     """
#     Step 1: Get the Link using 'mweb' (Mobile Web) Client.
#     Why? 
#     - 'ios' client CRASHES if cookies are used.
#     - 'android' client CRASHES because of PO Token.
#     - 'mweb' mimics Safari on iPhone. It accepts cookies AND gives m3u8.
#     """
#     selected_ua = random.choice(USER_AGENTS)
    
#     ydl_opts = {
#         # 1. ENABLE COOKIES (Safe with mweb)
#         'cookiefile': COOKIES_FILE, 
        
#         'http_headers': {
#             'User-Agent': selected_ua,
#             'Referer': 'https://www.youtube.com/',
#         },
        
#         # 2. FORMAT SELECTOR
#         # We relax it slightly to ensure we get *something* even if 1080p m3u8 isn't perfect
#         'format': 'best[height=1080][protocol^=m3u8]/bestvideo[height=1080][ext=mp4]+bestaudio[ext=m4a]/best[protocol^=m3u8]/best',
        
#         'quiet': True,
#         'logger': MyYtLogger(),
        
#         # 3. USE MWEB CLIENT (The Fix)
#         'extractor_args': {'youtube': {'player_client': ['mweb']}},
#     }

#     loop = asyncio.get_event_loop()
#     info = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(youtube_url, download=False))
    
#     url_list = []
#     if 'requested_formats' in info:
#         url_list = [f['url'] for f in info['requested_formats']]
#     elif 'url' in info:
#         url_list = [info['url']]
#     else:
#         raise Exception("No stream URL found")

#     title = info.get('title', 'video')
    
#     # 4. Extract Cookies for FFmpeg
#     cookie_header = parse_cookie_file(COOKIES_FILE)
    
#     # Extract UA used by yt-dlp
#     headers = info.get('http_headers', {})
#     final_ua = headers.get('User-Agent', selected_ua)
    
#     return url_list, title, final_ua, cookie_header

# async def generate_stream(url_list, user_agent, cookie_header):
#     """
#     Step 2: Stream with ALL Headers.
#     """
#     headers = f"User-Agent: {user_agent}\r\nReferer: https://www.youtube.com/\r\n"
#     if cookie_header:
#         headers += f"Cookie: {cookie_header}\r\n"

#     ffmpeg_cmd = [
#         'ffmpeg',
#         '-reconnect', '1', 
#         '-reconnect_streamed', '1', 
#         '-reconnect_delay_max', '5',
#         '-loglevel', 'warning',
#         '-headers', headers,
#         '-user_agent', user_agent, 
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
#         stderr=asyncio.subprocess.PIPE 
#     )

#     try:
#         while True:
#             chunk = await process.stdout.read(32 * 1024)
#             if not chunk:
#                 break
#             yield chunk
            
#         await process.wait()
#         if process.returncode != 0:
#             error_data = await process.stderr.read()
#             if error_data:
#                 logger.error(f"FFMPEG LOG: {error_data.decode()}")

#     except Exception as e:
#         logger.error(f"Stream Loop Failed: {e}")
#         try:
#             process.kill()
#         except:
#             pass
#     finally:
#         try:
#             process.kill()
#         except:
#             pass




#Gemini2
import asyncio
import logging
import yt_dlp
import urllib.parse
from config import COOKIES_FILE

logger = logging.getLogger(__name__)

class MyYtLogger:
    def debug(self, msg): pass
    def warning(self, msg): logger.warning(f"[yt-dlp] {msg}")
    def error(self, msg): logger.error(f"[yt-dlp] {msg}")

async def get_stream_url(youtube_url: str):
    """
    Step 1: Get the Link using the 'Smart TV' Client (Bypasses PO Token).
    """
    ydl_opts = {
        'cookiefile': COOKIES_FILE, # ✅ Enable cookies for stability
        
        # 1. Use 'tv' client to bypass PO Token & JS challenges
        'extractor_args': {'youtube': {'player_client': ['tv']}},
        
        # 2. Relaxed Format: TV streams are almost always HLS (m3u8)
        # We look for the best available m3u8.
        'format': 'best[protocol^=m3u8]/best',
        
        'quiet': True,
        'logger': MyYtLogger(),
    }

    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(youtube_url, download=False))
    
    url_list = []
    if 'requested_formats' in info:
        url_list = [f['url'] for f in info['requested_formats']]
    elif 'url' in info:
        url_list = [info['url']]
    else:
        raise Exception("No stream URL found")

    # 3. EXTRACT IDENTITY
    # We must pass the TV User-Agent to FFmpeg so it matches
    headers = info.get('http_headers', {})
    user_agent = headers.get('User-Agent', 'Mozilla/5.0')
    cookie_header = headers.get('Cookie', None)

    title = info.get('title', 'video')
    return url_list, title, user_agent, cookie_header

async def generate_stream(url_list, user_agent, cookie_header):
    """
    Step 2: Stream using the Identity from Step 1.
    """
    # Construct Headers
    headers_str = f"User-Agent: {user_agent}\r\n"
    if cookie_header:
        headers_str += f"Cookie: {cookie_header}\r\n"

    ffmpeg_cmd = [
        'ffmpeg',
        '-y',
        '-loglevel', 'warning',
        
        # Network robustness
        '-reconnect', '1', 
        '-reconnect_streamed', '1', 
        '-reconnect_delay_max', '5',
        
        # IDENTITY: Pass the Headers
        '-headers', headers_str,
        '-user_agent', user_agent,
        
        '-i', url_list[0],
    ]

    if len(url_list) > 1:
        ffmpeg_cmd.extend(['-i', url_list[1]])
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
        stderr=asyncio.subprocess.PIPE
    )

    try:
        while True:
            chunk = await process.stdout.read(32 * 1024)
            if not chunk:
                if process.returncode is not None and process.returncode != 0:
                    err = await process.stderr.read()
                    logger.error(f"FFmpeg Crash: {err.decode()}")
                break
            yield chunk
    except Exception as e:
        logger.error(f"Stream Error: {e}")
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