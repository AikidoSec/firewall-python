"""
Aikido agent, this will create a new thread and listen for stuff sent by our sources and sinks
"""

import time
import os
from multiprocessing.connection import Listener, Client
from multiprocessing import Process
from aikido_firewall.helpers.logging import logger

AGENT_SEC_INTERVAL = 5
IPC_ADDRESS = ("localhost", 9898)  # Specify the IP address and port


class AikidoProc:
    """
    Our agent thread
    """

    def __init__(self, address, key):
        logger.debug("Agent thread started")
        listener = Listener(address, authkey=key)
        self.queue = []
        while True:
            conn = listener.accept()
            logger.debug("connection accepted from %s", listener.last_accepted)
            while True:
                data = conn.recv()
                logger.error(data) # Temporary debugging
                if data[0] == "SQL_INJECTION":
                    self.queue.append(data[1])
                elif data[0] == "CLOSE":
                    conn.close()
                    break

    def report_to_agent(self):
        """
        Reports the found data to an Aikido server
        """
        logger.debug("Reporting to aikido server")
        # Implement


# pylint: disable=invalid-name # This variable does change
ipc = None


def get_ipc():
    """Returns the globally stored agent"""
    return ipc


def start_ipc():
    """
    Starts a thread to handle incoming/outgoing data
    """
    # pylint: disable=global-statement # We need this to be global
    global ipc

    if not "AIKIDO_SECRET_KEY" in os.environ:
        raise EnvironmentError("AIKIDO_SECRET_KEY is not set.")
    ipc = IPC(IPC_ADDRESS, os.environ["AIKIDO_SECRET_KEY"])
    ipc.start_aikido_listener()


class IPC:
    """Agent class"""

    def __init__(self, address, key):
        self.address = address
        self.key = str.encode(key)
        self.agent_proc = None

    def start_aikido_listener(self):
        """This will start the aikido thread which listens"""
        self.agent_proc = Process(
            target=AikidoProc,
            args=(
                self.address,
                self.key,
            ),
        )
        logger.debug("Starting a new agent thread")
        self.agent_proc.start()

    def send_data(self, action, obj):
        """This creates a new client for comms to the thread"""
        try:
            conn = Client(self.address, authkey=self.key)
            logger.debug("Created connection %s", conn)
            conn.send((action, obj))
            conn.send(("CLOSE", {}))
            conn.close()
            logger.debug("Connection closed")
        except Exception as e:
            logger.info("Failed to send data to agent %s", e)
