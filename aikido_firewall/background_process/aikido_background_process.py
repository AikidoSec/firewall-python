"""
Simply exports the aikido background process
"""

import multiprocessing.connection as con
import os
import time
import signal
import sched
from threading import Thread
from queue import Queue
from aikido_firewall.helpers.logging import logger
from aikido_firewall.background_process.reporter import Reporter
from aikido_firewall.helpers.should_block import should_block
from aikido_firewall.helpers.token import get_token_from_env
from aikido_firewall.background_process.api.http_api import ReportingApiHTTP


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
        self.reporter = None
        # Start reporting thread :
        Thread(target=self.reporting_thread).start()

        while True:
            conn = listener.accept()
            logger.debug("connection accepted from %s", listener.last_accepted)
            while True:
                data = conn.recv()  #  because of this no sleep needed in thread
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
                elif data[0] == "READ_PROPERTY":
                    if hasattr(self.reporter, data[1]):
                        conn.send(self.reporter.__dict__[data[1]])

    def reporting_thread(self):
        """Reporting thread"""
        logger.debug("Started reporting thread")
        event_scheduler = sched.scheduler(
            time.time, time.sleep
        )  # Create an event scheduler
        self.send_to_reporter(event_scheduler)

        api = ReportingApiHTTP("http://app.local.aikido.io/")
        # We need to pass along the scheduler so that the heartbeat also gets sent
        self.reporter = Reporter(
            should_block(), api, get_token_from_env(), False, event_scheduler
        )

        event_scheduler.run()

    def send_to_reporter(self, event_scheduler):
        """
        Reports the found data to an Aikido server
        """
        # Add back to event scheduler in REPORT_SEC_INTERVAL secs :
        event_scheduler.enter(
            REPORT_SEC_INTERVAL, 1, self.send_to_reporter, (event_scheduler,)
        )
        logger.debug("Checking queue")
        while not self.queue.empty():
            attack = self.queue.get()
            logger.debug("Reporting attack : %s", attack)
            self.reporter.on_detected_attack(attack[0], attack[1])
