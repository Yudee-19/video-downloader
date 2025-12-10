# import yt_dlp
# import json
# import subprocess
# import os

# # --- CONFIGURATION ---
# URL = "https://youtu.be/lZWaDmUlRJo?si=drqKK7QOLUKO-ECM"
# COOKIES_PATH = "/home/rareboy/Internship/Kajkarma/video-downloader/backend/cookies.txt"  # Adjust if your file is elsewhere
# OUTPUT_FILE = "final_test.mp4"

# def phase_1_dump_json():
#     print(f"\n🚀 PHASE 1: Dumping JSON from YouTube (Client: Web)...")
    
#     # We use the library directly (same as running yt-dlp --dump-json)
#     ydl_opts = {
#         'cookiefile': COOKIES_PATH,
#         'quiet': True,
#         'no_warnings': True,
#         # We start with standard 'web' as you requested. 
#         # If this fails, we change this single line to 'tv' or 'ios'.
#         # 'extractor_args': {'youtube': {'player_client': ['web']}}, 
#     }

#     try:
#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             info = ydl.extract_info(URL, download=False)
            
#             # Save to file just so you can inspect it manually if needed
#             with open("debug_dump.json", "w") as f:
#                 json.dump(info, f, indent=2)
                
#             print("✅ Phase 1 Complete. JSON saved to 'debug_dump.json'.")
#             return info
#     except Exception as e:
#         print(f"❌ Phase 1 Failed: {e}")
#         return None

# def phase_2_extract_data(info_json):
#     print(f"\n🚀 PHASE 2: finding the 'm3u8' treasure map...")
    
#     stream_url = None
#     user_agent = None
    
#     # 1. Extract the User-Agent used by Phase 1 (Crucial for Identity)
#     if 'http_headers' in info_json:
#         user_agent = info_json['http_headers'].get('User-Agent')
    
#     if not user_agent:
#         # Fallback if JSON is weird
#         user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" 

#     # 2. Find the m3u8 link
#     # We look through 'formats' to find the one with protocol='m3u8_native'
#     formats = info_json.get('formats', [])
#     for f in formats:
#         # Condition: Must be m3u8 AND have audio (acodec != none)
#         if 'm3u8' in f.get('protocol', '') and f.get('acodec') != 'none':
#             stream_url = f['url']
#             print(f"✅ Found candidate format: {f.get('format_id')} - {f.get('resolution')}")
#             # We prefer higher quality, so we keep searching, but this is a valid one.
#             # (In a real app, we'd sort by resolution, but taking the last one is usually best quality)
            
#     if stream_url:
#         print(f"✅ Phase 2 Complete.")
#         print(f"🔗 URL: {stream_url[:50]}...")
#         print(f"👤 UA: {user_agent[:30]}...")
#         return stream_url, user_agent
#     else:
#         print("❌ Phase 2 Failed: No valid m3u8 stream found in the JSON.")
#         return None, None

# def phase_3_ffmpeg(stream_url, user_agent):
#     print(f"\n🚀 PHASE 3: Running FFmpeg (The Zero-CPU Convert)...")
    
#     # We construct the headers string manually
#     headers_str = f"User-Agent: {user_agent}\r\nReferer: https://www.youtube.com/\r\n"
    
#     # Read the cookie file content manually to pass to FFmpeg
#     # (FFmpeg needs the literal string "Cookie: key=val", not a file path usually for headers)
#     # But for simplicity, let's try just UA first. If it fails, we add cookies string.
    
#     cmd = [
#         "ffmpeg",
#         "-y",               # Overwrite output
#         "-loglevel", "error", # Only show errors
#         "-reconnect", "1",
#         "-reconnect_streamed", "1",
        
#         # IDENTITY MATCHING
#         "-user_agent", user_agent, 
#         "-headers", headers_str,
        
#         "-i", stream_url,
        
#         # ZERO CPU FLAGS
#         "-c", "copy",
#         "-f", "mp4",
#         OUTPUT_FILE
#     ]
    
#     print(f"Running command: {' '.join(cmd)}")
    
#     try:
#         subprocess.run(cmd, check=True)
#         print(f"\n✅ Phase 3 Complete! File saved as {OUTPUT_FILE}")
        
#         if os.path.exists(OUTPUT_FILE) and os.path.getsize(OUTPUT_FILE) > 0:
#             print("🎉 SUCCESS: We have a valid video file.")
#         else:
#             print("⚠️ File created but size is 0 bytes.")
            
#     except subprocess.CalledProcessError as e:
#         print(f"❌ Phase 3 Failed: FFmpeg crashed.")

# if __name__ == "__main__":
#     # 1. Run Phase 1
#     data = phase_1_dump_json()
    
#     if data:
#         # 2. Run Phase 2
#         url, ua = phase_2_extract_data(data)
        
#         if url and ua:
#             # 3. Run Phase 3
#             phase_3_ffmpeg(url, ua)


import yt_dlp
import json
import subprocess
import os

# --- CONFIGURATION ---
URL = "https://youtu.be/lZWaDmUlRJo?si=drqKK7QOLUKO-ECM"
COOKIES_PATH = "./backend/cookies.txt"  
OUTPUT_FILE = "final_test.mp4"

def parse_cookie_file(cookie_file):
    """
    Reads the Netscape cookies.txt and converts it to a header string:
    'Cookie: key1=value1; key2=value2;'
    """
    if not os.path.exists(cookie_file):
        print(f"⚠️ Warning: Cookie file not found at {cookie_file}")
        return ""
    
    cookies = []
    try:
        with open(cookie_file, 'r') as f:
            for line in f:
                if not line.startswith('#') and line.strip():
                    fields = line.strip().split('\t')
                    if len(fields) >= 7:
                        name = fields[5]
                        value = fields[6]
                        cookies.append(f"{name}={value}")
        return "; ".join(cookies)
    except Exception as e:
        print(f"❌ Cookie Parse Error: {e}")
        return ""

def phase_1_dump_json():
    print(f"\n🚀 PHASE 1: Dumping JSON from YouTube...")
    
    ydl_opts = {
        'cookiefile': COOKIES_PATH,
        'quiet': True,
        'no_warnings': True,
        # REMOVED extractor_args as per your success
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(URL, download=False)
            print("✅ Phase 1 Complete.")
            return info
    except Exception as e:
        print(f"❌ Phase 1 Failed: {e}")
        return None

def phase_2_extract_data(info_json):
    print(f"\n🚀 PHASE 2: Finding the 'm3u8' treasure map...")
    
    stream_url = None
    # 1. Extract the User-Agent used by yt-dlp
    user_agent = info_json.get('http_headers', {}).get('User-Agent', "Mozilla/5.0")

    # 2. Find the m3u8 link (Format 301 is usually the best HLS)
    formats = info_json.get('formats', [])
    for f in formats:
        # We look for m3u8 protocol AND audio codec
        if 'm3u8' in f.get('protocol', '') and f.get('acodec') != 'none':
            stream_url = f['url']
            print(f"✅ Found candidate format: {f.get('format_id')} - {f.get('resolution')}")
            
    if stream_url:
        print(f"✅ Phase 2 Complete.")
        return stream_url, user_agent
    else:
        print("❌ Phase 2 Failed: No valid m3u8 stream found.")
        return None, None

def phase_3_ffmpeg(stream_url, user_agent):
    print(f"\n🚀 PHASE 3: Running FFmpeg (The Zero-CPU Convert)...")
    
    # 1. PARSE COOKIES
    cookie_str = parse_cookie_file(COOKIES_PATH)
    
    # 2. CONSTRUCT HEADERS CAREFULLY
    headers_str = f"User-Agent: {user_agent}\r\nReferer: https://www.youtube.com/\r\n"
    if cookie_str:
        headers_str += f"Cookie: {cookie_str}\r\n"

    cmd = [
        "ffmpeg",
        "-y",
        "-loglevel", "error",
        
        # FIX 1: Correct Flag Name
        "-protocol_whitelist", "file,http,https,tcp,tls,crypto",
        
        # FIX 2: Force Headers on Every Segment (The 403 Fix)
        "-http_persistent", "0",
        
        # Network reliability
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "5",
        
        # IDENTITY
        "-user_agent", user_agent,
        "-headers", headers_str,
        
        # INPUT
        "-i", stream_url,
        
        # ZERO CPU COPY
        "-c", "copy",
        "-f", "mp4",
        "-movflags", "frag_keyframe+empty_moov",
        OUTPUT_FILE
    ]
    
    print(f"Running command with headers...")
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ Phase 3 Complete! File saved as {OUTPUT_FILE}")
        
        # Verification
        if os.path.exists(OUTPUT_FILE) and os.path.getsize(OUTPUT_FILE) > 0:
             print(f"🎉 SUCCESS! Size: {os.path.getsize(OUTPUT_FILE) / (1024*1024):.2f} MB")
        else:
             print("❌ FAILED! File is 0MB.")
             
    except subprocess.CalledProcessError as e:
        print(f"❌ Phase 3 Failed: FFmpeg crashed.")

        
if __name__ == "__main__":
    data = phase_1_dump_json()
    if data:
        url, ua = phase_2_extract_data(data)
        if url and ua:
            phase_3_ffmpeg(url, ua)