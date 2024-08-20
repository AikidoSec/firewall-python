"""
Simply exports the aikido background process
"""

import multiprocessing.connection as con
import time
import sched
import traceback
import sys
from threading import Thread
from queue import Queue
from aikido_firewall.helpers.logging import logger
from aikido_firewall.background_process.reporter import Reporter
from aikido_firewall.helpers.check_env_for_blocking import check_env_for_blocking
from aikido_firewall.helpers.token import get_token_from_env
from aikido_firewall.background_process.api.http_api import ReportingApiHTTP
from .commands import process_incoming_command

EMPTY_QUEUE_INTERVAL = 5  # 5 seconds


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
                "Aikido listener may already be running on port %s, exiting", address[1]
            )
            sys.exit(0)
        self.queue = Queue()
        self.reporter = None
        # Start reporting thread :
        Thread(target=self.reporting_thread).start()

        while True:
            conn = listener.accept()
            logger.debug("connection accepted from %s", listener.last_accepted)
            while True:
                try:
                    data = conn.recv()  #  because of this no sleep needed in thread
                    logger.debug("Incoming data : %s", data)
                    process_incoming_command(bg_process=self, obj=data, conn=conn)
                    conn.close()  # Sort of EOL for Python IPC
                    break
                except Exception as e:
                    logger.error("Exception occured in server thread : %s", e)
                    logger.debug("Trace \n %s", traceback.format_exc())
                    break  # Return back to listening for new connections

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
            block=check_env_for_blocking(),
            api=api,
            token=get_token_from_env(),
            serverless=False,
        )
        time.sleep(2)  # Sleep 2 seconds to make sure modules get reported
        self.reporter.start(event_scheduler)

        event_scheduler.run()

    def send_to_reporter(self, event_scheduler):
        """
        Reports the found data to an Aikido server
        """
        # Add back to event scheduler in EMPTY_QUEUE_INTERVAL secs :
        event_scheduler.enter(
            EMPTY_QUEUE_INTERVAL, 1, self.send_to_reporter, (event_scheduler,)
        )
        logger.debug("Checking queue")
        while not self.queue.empty():
            attack = self.queue.get()
            logger.debug("Reporting attack : %s", attack)
            self.reporter.on_detected_attack(attack[0], attack[1])
