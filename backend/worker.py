import sys
import os
import logging
from redis import Redis
from rq import Worker, Queue, Connection
from config import redis_client, REDIS_HOST, REDIS_PORT

logging.basicConfig(level=logging.INFO, format="%(asctime)s [WORKER] %(message)s")
logger = logging.getLogger(__name__)

# Ensure core is importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def start_worker():
    if not redis_client:
        logger.error("❌ Redis NOT connected! Worker cannot start.")
        sys.exit(1)

    with Connection(redis_client):
        queues = ['default']
        logger.info(f"👷 Worker STARTED. Listening on: {queues}")
        
        # The worker will automatically find 'core.process_single_job' 
        # because we are in the same directory.
        w = Worker(queues)
        w.work()

if __name__ == '__main__':
    start_worker()