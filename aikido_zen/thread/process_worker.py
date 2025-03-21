import multiprocessing
import time

from aikido_zen.helpers.logging import logger
from aikido_zen.thread import thread_cache

# Renew the cache from this background worker every 5 seconds
RENEW_CACHE_EVERY_X_SEC = 5


def aikido_process_worker_thread():
    """
    process worker -> When a web server like gUnicorn makes new processes, and those have multiple threads,
    Aikido process worker is linked to those new processes, so in essence it's 1 extra thread. This thread
    is responsible for syncing statistics, route data, configuration, ...
    """
    # Get the current process
    current_process = multiprocessing.current_process()

    while True:
        # Print information about the process
        logger.debug(
            f"Process ID: {current_process.pid}, Name: {current_process.name} - process_worker renewing thread cache."
        )

        # Renew the cache every 5 seconds
        thread_cache.renew()
        time.sleep(RENEW_CACHE_EVERY_X_SEC)
