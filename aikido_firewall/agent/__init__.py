"""
Aikido agent, this will create a new thread and listen for stuff sent by our sources and sinks
"""

import time
import queue
from threading import Thread
from aikido_firewall.helpers.logging import logger

AIKIDO_IPC_PORT = 49155
AGENT_SEC_INTERVAL = 0.05


def thread_function(q):
    """
    Function that will be the starting point of our new thread
    """
    while True:
        while not q.empty():
            item = q.get()
            logger.debug("Agent %s", item)
        time.sleep(AGENT_SEC_INTERVAL)


def start_agent():
    """
    Starts a thread to handle incoming/outgoing data
    """
    # This creates a queue for Inter-Process Communication
    logger.debug("Creating IPC Queue")
    q = queue.Queue()

    logger.debug("Starting a new agent thread")
    agent_thread = Thread(target=thread_function, args=(q,))
    agent_thread.start()
    logger.debug("Agent thread started")
    return Agent(q)


class Agent:
    """Agent class"""

    def __init__(self, q):
        self.q = q

    def report(self, obj, action):
        """
        Report something to the agent
        """
        self.q.put((action, obj))
