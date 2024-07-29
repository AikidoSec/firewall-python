"""
Aikido background process, this will create a new process
and listen for data sent by our sources and sinks
"""

import time
import os
import secrets
import signal
import socket
import multiprocessing.connection as con
from multiprocessing import Process
from threading import Thread
from queue import Queue
from aikido_firewall.helpers.logging import logger
from aikido_firewall.background_process.reporter import Reporter
from aikido_firewall.helpers.should_block import should_block
from aikido_firewall.helpers.token import get_token_from_env

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
        try:
            listener = con.Listener(address, authkey=key)
        except OSError:
            logger.warning(
                "Aikido listener may already be running on port %s", address[1]
            )
            pid = os.getpid()
            os.kill(pid, signal.SIGTERM)  # Kill this subprocess
        self.queue = Queue()
        api = ReportingApiHTTP("http://app.local.aikido.io/")
        self.reporter = Reporter(should_block(), api, get_token_from_env(), False)
        # Start reporting thread :
        Thread(target=self.reporting_thread).start()

        while True:
            conn = listener.accept()
            logger.debug("connection accepted from %s", listener.last_accepted)
            while True:
                data = conn.recv()
                logger.debug("Incoming data : %s", data)
                if data[0] == "ATTACK":
                    self.queue.put(data[1])
                elif data[0] == "CLOSE":
                    conn.close()
                    break
                elif data[0] == "KILL":
                    logger.debug("Killing subprocess")
                    conn.close()
                    pid = os.getpid()
                    os.kill(pid, signal.SIGTERM)  # Kill this subprocess

    def reporting_thread(self):
        """Reporting thread"""
        logger.debug("Started reporting thread")
        self.reporter = Reporter(should_block(), {}, get_token_from_env(), None)
        logger.debug("Created Reporter")
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


def reset_comms():
    """This will reset communications"""
    global ipc
    if ipc:
        ipc.send_data("KILL", {})
        ipc = None


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
        # The key needs to be in byte form
        self.address = address
        self.key = key

    def start_aikido_listener(self):
        """This will start the aikido process which listens"""
        pid = os.fork()
        if pid == 0:  # Child process
            AikidoBackgroundProcess(self.address, self.key)
        else:  # Parent process
            logger.debug("Started background process, PID: %d", pid)

    def send_data(self, action, obj):
        """
        This creates a new client for comms to the background process
        """

        # We want to make sure that sending out this data affects the process as little as possible
        # So we run it inside a seperate thread with a timeout of 3 seconds
        def target(address, key, data_array):
            try:
                conn = con.Client(address, authkey=key)
                logger.debug("Created connection %s", conn)
                for data in data_array:
                    conn.send(data)
                conn.send(("CLOSE", {}))
                conn.close()
                logger.debug("Connection closed")
            except Exception as e:
                logger.info("Failed to send data to bg process : %s", e)

        t = Thread(
            target=target, args=(self.address, self.key, [(action, obj)]), daemon=True
        )
        t.start()
        t.join(timeout=3)
