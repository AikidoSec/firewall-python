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
from aikido_firewall.background_process.api.http_api import ReportingApiHTTP

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
                elif data[0] == "READ_PROPERTY":
                    if hasattr(self.reporter, data[1]):
                        conn.send(self.reporter.__dict__[data[1]])

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
        logger.debug("Checking queue")
        while not self.queue.empty():
            attack = self.queue.get()
            logger.debug("Reporting attack : %s", attack)
            self.reporter.on_detected_attack(attack[0], attack[1])


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
        def target(address, key, data):
            try:
                conn = con.Client(address, authkey=key)
                logger.debug("Created connection %s", conn)
                conn.send(data)
                conn.send(("CLOSE", {}))
                conn.close()
                logger.debug("Connection closed")
            except Exception as e:
                logger.info("Failed to send data to bg process : %s", e)

        t = Thread(
            target=target, args=(self.address, self.key, (action, obj)), daemon=True
        )
        t.start()
        t.join(timeout=3)

    def poll_config(self, prop):
        """
        This will poll the config from the Background Process
        """
        conn = con.Client(self.address, authkey=self.key)
        conn.send(("READ_PROPERTY", prop))
        prop_value = conn.recv()
        conn.send(("CLOSE", {}))
        conn.close()
        logger.debug("Received property %s as %s", prop, prop_value)
        return prop_value
