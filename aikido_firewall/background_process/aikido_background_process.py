"""
Simply exports the aikido background process
"""

import multiprocessing.connection as con
import time
import sched
import sys
from threading import Thread
from queue import Queue
from aikido_firewall.helpers.logging import logger
from aikido_firewall.background_process.reporter import Reporter
from aikido_firewall.helpers.should_block import should_block
from aikido_firewall.helpers.token import get_token_from_env
from aikido_firewall.background_process.api.http_api import ReportingApiHTTP
from aikido_firewall.ratelimiting import should_ratelimit_request


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
                        sys.exit(0)
                    elif data[0] == "READ_PROPERTY":  # meant to get config props
                        if hasattr(self.reporter, data[1]):
                            conn.send(self.reporter.__dict__[data[1]])
                        else:
                            logger.debug(
                                "Reporter has no attribute %s, current reporter: %s",
                                data[1],
                                self.reporter,
                            )
                            conn.send(None)
                    elif data[0] == "ROUTE":
                        # Called every time the user visits a route
                        self.reporter.routes.add_route(
                            method=data[1][0], path=data[1][1]
                        )
                    elif data[0] == "SHOULD_RATELIMIT":
                        # Called to check if the context passed along as data should be
                        # Rate limited
                        conn.send(
                            should_ratelimit_request(
                                context=data[1], reporter=self.reporter
                            )
                        )
                except Exception as e:
                    logger.error("Exception occured in server thread : %s", e)

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
            block=should_block(),
            api=api,
            token=get_token_from_env(),
            serverless=False,
            event_scheduler=event_scheduler,
        )

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
