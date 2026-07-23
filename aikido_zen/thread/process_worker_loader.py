import multiprocessing
import threading

from aikido_zen.context import get_current_context
from aikido_zen.helpers.logging import logger
from aikido_zen.thread import thread_cache
from aikido_zen.thread.process_worker import aikido_process_worker_thread

_load_worker_lock = threading.Lock()


def load_worker():
    """
    Loads in a new process worker if one does not already exist for the current process
    """
    if get_current_context() is None:
        return  # don't start a worker if it's not related to a request.

    # The name is aikido-process-worker- + the current PID
    thread_name = "aikido-process-worker-" + str(multiprocessing.current_process().pid)

    with _load_worker_lock:
        # The first HTTP request in a worker process may arrive before its local cache
        # has received config. Synchronize with the background process immediately
        # instead of waiting for the periodic sync.
        if not thread_cache.is_config_loaded():
            try:
                thread_cache.renew()
            except Exception as e:
                logger.warning("An error occurred during data synchronization: %s", e)

        # Each worker process should have only one periodic synchronization thread.
        if any(thread.name == thread_name for thread in threading.enumerate()):
            return

        # Create a new daemon thread tht will handle communication to and from background agent
        thread = threading.Thread(target=aikido_process_worker_thread, name=thread_name)
        thread.daemon = True
        thread.start()
