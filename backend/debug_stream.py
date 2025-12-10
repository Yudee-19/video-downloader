import asyncio
import yt_dlp
import os

# CONFIG
TEST_URL = "https://youtu.be/lZWaDmUlRJo?si=drqKK7QOLUKO-ECM"

# Custom Logger
class MyYtLogger:
    def debug(self, msg): pass
    def warning(self, msg): print(f"[yt-dlp WARN] {msg}")
    def error(self, msg): print(f"[yt-dlp ERROR] {msg}")

async def run_debug():
    print("----------------------------------------------------------------")
    print("🕵️  STARTING SURGERY DEBUG")
    print("----------------------------------------------------------------")

    # 1. Get URL (No Cookies)
    print("1. Fetching URL via yt-dlp...")
    ydl_opts = {
        'format': 'best[height=1080][protocol^=m3u8]/bestvideo[height=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'logger': MyYtLogger(),
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(TEST_URL, download=False)
        if 'url' in info:
            stream_url = info['url']
        elif 'requested_formats' in info:
            stream_url = info['requested_formats'][0]['url']
        else:
            print("❌ No URL found.")
            return

    print(f"✅ URL Found: {stream_url[:50]}...")

    # 2. RUN FFMPEG (File Mode first to verify permission/execution)
    output_filename = "debug_video.mp4"
    if os.path.exists(output_filename): os.remove(output_filename)

    print("\n2. Launching FFmpeg (FILE MODE check)...")
    print("   We are adding '-report' to generate a log file.")
    
    # We set the environment variable 'FFREPORT' to save the log
    os.environ["FFREPORT"] = "file=ffmpeg_debug.log:level=32"

    ffmpeg_cmd = [
        'ffmpeg',
        '-y',
        '-i', stream_url,
        '-c', 'copy',
        output_filename
    ]

    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    print(f"   PID: {process.pid}")
    
    # Wait for 5 seconds then kill it (just to see if it starts)
    try:
        await asyncio.wait_for(process.wait(), timeout=10.0)
    except asyncio.TimeoutError:
        print("   ⏳ FFmpeg is running... (This is GOOD)")
        process.kill()
        print("   killed process for test.")
    
    # Check if log file was created
    if os.path.exists("ffmpeg_debug.log"):
        print("\n✅ 'ffmpeg_debug.log' was created!")
        print("👇 HERE IS THE END OF THE LOG (Why it failed/worked):")
        with open("ffmpeg_debug.log", "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            print("".join(lines[-20:])) # Print last 20 lines
    else:
        print("\n❌ NO LOG FILE. FFmpeg didn't even start.")
        stderr = await process.stderr.read()
        print(f"   Python captured stderr: {stderr.decode()}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(run_debug())