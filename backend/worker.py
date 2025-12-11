import sys
import os
import logging
from rq import Worker, Queue
from config import redis_client, redis_raw_client, REDIS_HOST

logging.basicConfig(level=logging.INFO, format="%(asctime)s [WORKER] %(message)s")
logger = logging.getLogger(__name__)

# Ensure core is importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# def start_worker():
#     if not redis_client:
#         logger.error("❌ Redis NOT connected! Worker cannot start.")
#         sys.exit(1)

#     queues = [Queue("default", connection=redis_client)]
#     logger.info("👷 Worker STARTED. Listening on: ['default']")

#     # In RQ 1.16+, pass connection directly to Worker
#     w = Worker(queues, connection=redis_client)
#     w.work()

def start_worker():
    if not redis_raw_client:
        logger.error("❌ Redis NOT connected! Worker cannot start.")
        sys.exit(1)

    # Use the RAW client here. RQ needs bytes, not strings.
    queues = ['default']
    logger.info(f"👷 Worker STARTED. Listening on: {queues}")
    
    try:
        # Pass the raw connection
        w = Worker(queues, connection=redis_raw_client)
        w.work()
    except Exception as e:
        logger.error(f"❌ Worker crashed: {e}")

if __name__ == '__main__':
    start_worker()