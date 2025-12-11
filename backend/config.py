import os
import sys
import logging
import asyncio
import redis
from concurrent.futures import ThreadPoolExecutor

# Server Configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("stream_log.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Asyncio Policy for Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

redis_client = None
redis_raw_client = None
try:
    redis_config = {
        'host': REDIS_HOST,
        'port': REDIS_PORT,
        'decode_responses': True,
        'socket_connect_timeout': 5,
        'socket_timeout': 5,
        'retry_on_timeout': True
    }
    redis_raw_config = redis_config.copy()
    redis_raw_config['decode_responses'] = False

    if REDIS_PASSWORD:
        redis_config['password'] = REDIS_PASSWORD
    
    redis_client = redis.Redis(**redis_config)
    redis_raw_client = redis.Redis(**redis_raw_config)
    redis_client.ping()
    print(f"✅ Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    print(f" Redis connection failed: {e}")
    print(" Falling back to in-memory storage (not recommended for production)")
    redis_client = None
    redis_raw_client = None

# Directories & Files
TEMP_DIR = os.getenv("TEMP_DIR", "tmp_videos")
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
os.makedirs(TEMP_DIR, exist_ok=True)

if BASE_DIR:
    print(f"✅ Base directory set to: {BASE_DIR}")
    COOKIES_FILE = os.path.join(BASE_DIR, "cookies.txt")
else:
    print("cookie file is not found")
    COOKIES_FILE = "/home/rareboy/Internship/Kajkarma/video-downloader/backend/cookies.txt"

# Thread Pool
MAX_PARALLEL_DOWNLOADS = int(os.getenv("MAX_PARALLEL_DOWNLOADS", "3"))
executor = ThreadPoolExecutor(max_workers=MAX_PARALLEL_DOWNLOADS)

# Constants
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:118.0) Gecko/20100101 Firefox/118.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]