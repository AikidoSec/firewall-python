import multiprocessing
import time

from aikido_zen.helpers.logging import logger
from aikido_zen.thread import thread_cache

# Renew the cache from this background worker every 15 seconds
RENEW_CACHE_EVERY_X_SEC = 15
INITIAL_CONFIG_RETRY_SECONDS = 1
INITIAL_CONFIG_RETRY_WINDOW_SECONDS = 15


def aikido_process_worker_thread():
    """
    process worker -> When a web server like gUnicorn makes new processes, and those have multiple threads,
    Aikido process worker is linked to those new processes, so in essence it's 1 extra thread. This thread
    is responsible for syncing statistics, route data, configuration, ...
    """
    # Get the current process
    current_process = multiprocessing.current_process()
    startup_deadline = time.monotonic() + INITIAL_CONFIG_RETRY_WINDOW_SECONDS

    while True:
        # Print information about the process
        logger.debug(
            "PID=%s Name=%s - process_worker renewing thread cache.",
            current_process.pid,
            current_process.name,
        )

        try:
            thread_cache.renew()
        except Exception as e:
            logger.warning("An error occurred during data synchronization: %s", e)

        if not thread_cache.is_config_loaded() and time.monotonic() < startup_deadline:
            time.sleep(INITIAL_CONFIG_RETRY_SECONDS)
        else:
            time.sleep(RENEW_CACHE_EVERY_X_SEC)
