import json
import random
import os
import subprocess
import yt_dlp
import boto3
from config import redis_client, TEMP_DIR, COOKIES_FILE, USER_AGENTS, logger


class MyYtLogger:
    """Custom logger to redirect yt-dlp output to our app logger."""

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


# In-memory fallback (Only used if Redis fails, which shouldn't happen in Prod)
download_status = {}

# Redis key prefixes
REDIS_DOWNLOAD_KEY = "download:"
REDIS_BATCH_KEY = "batch:"

# --- AWS CONFIG ---
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_BUCKET = os.getenv("AWS_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

s3_client = None
try:
    if AWS_ACCESS_KEY and AWS_SECRET_KEY:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION,
        )
        logger.info("✅ S3 Client Initialized")
    else:
        logger.warning("⚠️ AWS Credentials missing! S3 Uploads will fail.")
except Exception as e:
    logger.error(f"❌ Failed to init S3 Client: {e}")

# --- HELPER FUNCTIONS ---


def set_download_status(file_id: str, status: dict):
    if redis_client:
        try:
            redis_client.setex(
                f"{REDIS_DOWNLOAD_KEY}{file_id}", 3600, json.dumps(status)
            )
        except Exception as e:
            logger.error(f"Redis error: {e}")
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
            logger.error(f"Redis error: {e}")
            return download_status.get(file_id)
    else:
        return download_status.get(file_id)


def delete_download_status(file_id: str):
    if redis_client:
        try:
            redis_client.delete(f"{REDIS_DOWNLOAD_KEY}{file_id}")
        except Exception as e:
            logger.error(f"Redis error: {e}")
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
            logger.error(f"Redis error: {e}")
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
            logger.error(f"Redis error: {e}")
            return download_status.get(f"batch_{batch_id}")
    else:
        return download_status.get(f"batch_{batch_id}")


def upload_to_s3(file_path, object_name):
    """
    Uploads a file to S3 and returns a presigned URL.
    """
    if not s3_client:
        logger.error("❌ S3 Client not available")
        return None

    try:
        logger.info(f"☁️ Uploading {object_name} to S3...")
        s3_client.upload_file(file_path, AWS_BUCKET, object_name)

        # Generate URL (Valid for 1 hour)
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": AWS_BUCKET, "Key": object_name},
            ExpiresIn=3600,
        )
        logger.info(f"✅ Upload Success: {url}")
        return url
    except Exception as e:
        logger.error(f"❌ S3 Upload Failed: {e}")
        return None


# --- MAIN TASK FUNCTIONS ---


def download_video_task(
    file_id: str,
    url: str,
    start_time: str | None,
    end_time: str | None,
    audio_only: bool,
    is_batch: bool = False,
):
    """
    Downloads video to local TEMP_DIR.
    For single downloads (is_batch=False): Sets ready=True and stores filepath
    For batch downloads (is_batch=True): Returns filepath for S3 upload
    """
    final_filepath = None
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

        final_filepath = filename

        # --- Trimming Logic ---
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
                os.remove(filename)  # Delete original
                final_filepath = output_file
            except Exception as e:
                logger.error(f"Trimming failed: {e}")

        # For single downloads, set ready=True so user can download locally
        # For batch downloads, just return the path for S3 upload
        if not is_batch:
            set_download_status(
                file_id,
                {
                    "ready": True,
                    "filename": os.path.basename(final_filepath),
                    "filepath": final_filepath,
                    "error": None,
                    "progress": "100%",
                    "status": "completed",
                },
            )

        return final_filepath

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
        return None


def process_single_job(file_id, url, start_t, end_t, audio_only):
    """
    THE WRAPPER: Download -> Upload to S3 -> Delete Local
    This is what the Worker executes.
    """
    logger.info(f"⚙️ Processing Job: {file_id}")

    # 1. Download (is_batch=True so it returns filepath without setting ready=True)
    filepath = download_video_task(
        file_id, url, start_t, end_t, audio_only, is_batch=True
    )

    if filepath and os.path.exists(filepath):
        # 2. Upload to S3
        filename = os.path.basename(filepath)
        s3_key = f"downloads/{file_id}/{filename}"

        s3_url = upload_to_s3(filepath, s3_key)

        if s3_url:
            # 3. Update Redis with S3 Link
            set_download_status(
                file_id,
                {
                    "ready": True,
                    "filename": filename,
                    "filepath": None,  # Local path is gone
                    "download_url": s3_url,  # THE NEW S3 LINK
                    "error": None,
                    "progress": "100%",
                    "status": "completed",
                },
            )

            # 4. DELETE LOCAL FILE (Save Space)
            try:
                os.remove(filepath)
                logger.info(f"🗑️ Cleaned up local file: {filepath}")
            except Exception as e:
                logger.error(f"Failed to delete local file: {e}")
        else:
            set_download_status(
                file_id, {"status": "failed", "error": "S3 Upload Failed"}
            )
    else:
        # If download_video_task failed, it already updated Redis with the error
        logger.error(f"Job {file_id} failed during download phase.")
