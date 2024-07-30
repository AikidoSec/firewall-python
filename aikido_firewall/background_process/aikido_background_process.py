"""
Simply exports the aikido background process
"""

import multiprocessing.connection as con
import os
import time
import signal
from threading import Thread
from queue import Queue
from aikido_firewall.helpers.logging import logger

REPORT_SEC_INTERVAL = 600  # 10 minutes


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
                elif data[0] == "CLOSE":  # this is a kind of EOL for python IPC
                    conn.close()
                    break
                elif (
                    data[0] == "KILL"
                ):  # when main process quits , or during testing etc
                    logger.debug("Killing subprocess")
                    conn.close()
                    pid = os.getpid()
                    os.kill(pid, signal.SIGTERM)  # Kill this subprocess

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
