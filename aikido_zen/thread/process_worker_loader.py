import multiprocessing
import threading

from aikido_zen.context import get_current_context
from aikido_zen.thread.process_worker import aikido_process_worker_thread


def load_worker():
    """
    Loads in a new process worker if one does not already exist for the current process
    """
    if get_current_context() is None:
        return  # don't start a worker if it's not related to a request.

    # The name is aikido-process-worker- + the current PID
    thread_name = "aikido-process-worker-" + str(multiprocessing.current_process().pid)
    if any([thread.name == thread_name for thread in threading.enumerate()]):
        return  # The thread already exists, returning.

    # Create a new daemon thread tht will handle communication to and from background agent
    thread = threading.Thread(target=aikido_process_worker_thread, name=thread_name)
    thread.daemon = True
    thread.start()
