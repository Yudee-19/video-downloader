import json
import random
import os
import subprocess
import yt_dlp
from config import redis_client, TEMP_DIR, COOKIES_FILE, USER_AGENTS, logger

# In-memory fallback
download_status = {}

# Redis key prefixes (keep local since these are internal to core)
REDIS_DOWNLOAD_KEY = "download:"
REDIS_BATCH_KEY = (
    "batch:"  # Note: Also exported from config.py for main_v2.py cleanup endpoint
)


class MyYtLogger:
    def __init__(self, app_logger):
        self.logger = app_logger

    def debug(self, msg):
        if not msg.startswith("[debug] "):
            self.logger.info(f"[yt-dlp] {msg}")
        else:
            self.logger.info(f"{msg}")

    def warning(self, msg):
        self.logger.warning(f"[yt-dlp] {msg}")

    def error(self, msg):
        self.logger.error(f"[yt-dlp] {msg}")


def set_download_status(file_id: str, status: dict):
    if redis_client:
        try:
            redis_client.setex(
                f"{REDIS_DOWNLOAD_KEY}{file_id}", 3600, json.dumps(status)
            )
        except Exception as e:
            print(f"Redis error: {e}")
            download_status[file_id] = status
    else:
        download_status[file_id] = status


def get_download_status(file_id: str):
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
    if redis_client:
        try:
            redis_client.setex(f"{REDIS_BATCH_KEY}{batch_id}", 3600, json.dumps(status))
        except Exception as e:
            print(f"Redis error: {e}")
            download_status[f"batch_{batch_id}"] = status
    else:
        download_status[f"batch_{batch_id}"] = status


def get_batch_status(batch_id: str):
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


def download_video_task(
    file_id: str,
    url: str,
    start_time: str | None,
    end_time: str | None,
    audio_only: bool,
):
    try:
        set_download_status(
            file_id,
            {
                "ready": False,
                "filename": None,
                "filepath": None,
                "error": None,
                "progress": "0%",
                "status": "downloading",
            },
        )

        selected_user_agent = random.choice(USER_AGENTS)

        base_opts = {
            "outtmpl": f"{TEMP_DIR}/%(title)s.%(ext)s",
            "cookiefile": COOKIES_FILE,
            "http_headers": {
                "User-Agent": selected_user_agent,
                "Accept-Language": "en-US,en;q=0.9",
            },
            "retries": 5,
            "fragment_retries": 5,
        }

        if audio_only:
            ydl_opts = {
                **base_opts,
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
                "postprocessor_args": ["-ar", "44100"],
                "prefer_ffmpeg": True,
            }
        else:
            ydl_opts = {
                **base_opts,
                "format": "bestvideo+bestaudio/best",
                "merge_output_format": "mp4",
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            if audio_only:
                base_filename = os.path.splitext(filename)[0]
                filename = f"{base_filename}.mp3"

        if (start_time or end_time) and not audio_only:
            set_download_status(
                file_id,
                {
                    "ready": False,
                    "filename": None,
                    "filepath": None,
                    "error": None,
                    "progress": "90%",
                    "status": "trimming",
                },
            )

            base_filename = os.path.splitext(filename)[0]
            output_file = f"{base_filename}_trimmed.mp4"
            cmd = ["ffmpeg", "-i", filename]

            if start_time:
                cmd.extend(["-ss", start_time])
            if end_time:
                cmd.extend(["-to", end_time])

            cmd.extend(["-c", "copy", output_file])

            try:
                subprocess.run(cmd, check=True, capture_output=True)
                os.remove(filename)
                filename = output_file
            except Exception as e:
                print(f"Trimming failed: {e}")

        set_download_status(
            file_id,
            {
                "ready": True,
                "filename": os.path.basename(filename),
                "filepath": filename,
                "error": None,
                "progress": "100%",
                "status": "completed",
            },
        )

    except Exception as e:
        set_download_status(
            file_id,
            {
                "ready": False,
                "filename": None,
                "filepath": None,
                "error": str(e),
                "progress": "0%",
                "status": "failed",
            },
        )
