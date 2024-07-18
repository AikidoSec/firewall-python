"""
Aikido agent, this will create a new thread and listen for stuff sent by our sources and sinks
"""

import time
import queue
from threading import Thread
from aikido_firewall.helpers.logging import logger

AGENT_SEC_INTERVAL = 60


class AikidoThread:
    """
    Our agent thread
    """

    def __init__(self, q):
        logger.debug("Agent thread started")
        while True:
            while not q.empty():
                self.process_data(q.get())
        time.sleep(AGENT_SEC_INTERVAL)
        self.q = q
        self.current_context = None

    def process_data(self, item):
        """Will process the data added to the queue"""
        action, data = item
        logger.debug("Action %s, Data %s", action, data)
        if action == "REPORT":
            logger.debug("Report")
            self.current_context = data
        else:
            logger.error("Action `%s` is not defined. (Aikido Agent)", action)


# pylint: disable=invalid-name # This variable does change
agent = None


def get_agent():
    """Returns the globally stored agent"""
    return agent


def start_agent():
    """
    Starts a thread to handle incoming/outgoing data
    """
    # pylint: disable=global-statement # We need this to be global
    global agent

    # This creates a queue for Inter-Process Communication
    logger.debug("Creating IPC Queue")
    q = queue.Queue()

    logger.debug("Starting a new agent thread")
    agent_thread = Thread(target=AikidoThread, args=(q,))
    agent_thread.start()
    agent = Agent(q)


class Agent:
    """Agent class"""

    def __init__(self, q):
        self.q = q

    def report(self, obj, action):
        """
        Report something to the agent
        """
        self.q.put((action, obj))
