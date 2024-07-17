"""
Aikido agent, this will create a new thread and listen for stuff sent by our sources and sinks
"""

import time
from multiprocessing import Process, Queue
from aikido_firewall.helpers.logging import logger

AIKIDO_IPC_PORT = 49155
AGENT_SEC_INTERVAL = 0.05


def thread_function(queue):
    """
    Function that will be the starting point of our new thread
    """
    while True:
        while not queue.empty():
            item = queue.get()
            logger.debug(item)
        time.sleep(AGENT_SEC_INTERVAL)


def start_agent():
    """
    Starts a thread to handle incoming/outgoing data
    """
    # This creates a queue for Inter-Process Communication
    logger.debug("Creating IPC Queue")
    queue = Queue()

    logger.debug("Starting a new agent thread")
    agent_thread = Process(target=thread_function, args=(queue,))
    agent_thread.start()
    logger.debug("Agent thread started")
