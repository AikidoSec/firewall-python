"""
process worker -> When a web server like gUnicorn makes new processes, and those have multiple threads,
Aikido's process worker is linked to those new processes, so in essence it's 1 extra thread. This thread
is responsible for syncing statistics, route data, ...
"""
import multiprocessing
import threading
import time

from aikido_zen.helpers.logging import logger


def start_worker():
    # Find out the running process:
    logger.info("[%s](%s) <-- `%s`",
                 multiprocessing.current_process().name,
                 multiprocessing.current_process().pid,
                 threading.current_thread().name)

    # The name is aikido-process-worker- + the current PID
    thread_name = "aikido-process-worker-" + str(multiprocessing.current_process().pid)
    if any([thread.name == thread_name for thread in threading.enumerate()]):
        return # The thread already exists, returning.

    # Create a new daemon thread tht will handle communication to and from background agent
    thread = threading.Thread(target=aikido_process_worker_thread, name=thread_name)
    thread.daemon = True
    thread.start()


def aikido_process_worker_thread():
    # Get the current process
    current_process = multiprocessing.current_process()

    while True:
        # Print information about the process
        logger.info(f"Process ID: {current_process.pid}, Name: {current_process.name}")
        time.sleep(5)
