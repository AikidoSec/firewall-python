"""
Aikido background process, this will create a new process
and listen for data sent by our sources and sinks
"""

import time
import os
import secrets
import multiprocessing.connection as con
from multiprocessing import Process
from threading import Thread
from queue import Queue
from aikido_firewall.helpers.logging import logger

REPORT_SEC_INTERVAL = 600  # 10 minutes
IPC_ADDRESS = ("localhost", 9898)  # Specify the IP address and port


class AikidoBackgroundProcess:
    """
    Aikido's background process consists of 2 threads :
    - (main) Listening thread which listens on an IPC socket for incoming data
    - (spawned) reporting thread which will collect the IPC data and send it to a Reporter
    """

    def __init__(self, address, key):
        logger.debug("Background process started")
        listener = con.Listener(address, authkey=key)
        self.queue = Queue()
        # Start reporting thread :
        Thread(target=self.reporting_thread).start()

        while True:
            conn = listener.accept()
            logger.debug("connection accepted from %s", listener.last_accepted)
            while True:
                data = conn.recv()
                logger.error(data)  # Temporary debugging
                if data[0] == "SQL_INJECTION":
                    self.queue.put(data[1])
                elif data[0] == "CLOSE":
                    conn.close()
                    break

    def reporting_thread(self):
        """Reporting thread"""
        logger.debug("Started reporting thread")
        while True:
            self.send_to_reporter()
            time.sleep(REPORT_SEC_INTERVAL)

    def send_to_reporter(self):
        """
        Reports the found data to an Aikido server
        """
        items_to_report = []
        while not self.queue.empty():
            items_to_report.append(self.queue.get())
        logger.debug("Reporting to aikido server")
        logger.critical("Items to report : %s", items_to_report)
        # Currently not making API calls


# pylint: disable=invalid-name # This variable does change
ipc = None


def get_comms():
    """
    Returns the globally stored IPC object, which you need
    to communicate to our background process.
    """
    return ipc


def start_background_process():
    """
    Starts a process to handle incoming/outgoing data
    """
    # pylint: disable=global-statement # We need this to be global
    global ipc
    # Generate a secret key :
    generated_key_bytes = secrets.token_bytes(32)

    ipc = IPC(IPC_ADDRESS, generated_key_bytes)
    ipc.start_aikido_listener()


class IPC:
    """
    Facilitates Inter-Process communication
    """

    def __init__(self, address, key):
        self.address = address
        self.key = key
        self.background_process = None

    def start_aikido_listener(self):
        """
        This will start the aikido background process which listens
        and makes calls to the API
        """
        self.background_process = Process(
            target=AikidoBackgroundProcess,
            args=(
                self.address,
                self.key,
            ),
        )
        logger.debug("Starting the background process")
        self.background_process.start()

    def send_data(self, action, obj):
        """
        This creates a new client for comms to the background process
        """
        try:
            conn = con.Client(self.address, authkey=self.key)
            logger.debug("Created connection %s", conn)
            conn.send((action, obj))
            conn.send(("CLOSE", {}))
            conn.close()
            logger.debug("Connection closed")
        except Exception as e:
            logger.info("Failed to send data to bg process : %s", e)
