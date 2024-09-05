"""
Simply exports the aikido background process
"""

import multiprocessing.connection as con
import time
import os
import sched
import traceback
import sys
from threading import Thread
from queue import Queue
from aikido_firewall.helpers.logging import logger
from aikido_firewall.background_process.cloud_connection_manager import (
    CloudConnectionManager,
)
from aikido_firewall.helpers.check_env_for_blocking import check_env_for_blocking
from aikido_firewall.helpers.token import get_token_from_env
from aikido_firewall.background_process.api.http_api_ratelimited import (
    ReportingApiHTTPRatelimited,
)
from .commands import process_incoming_command

EMPTY_QUEUE_INTERVAL = 5  # 5 seconds


class AikidoBackgroundProcess:
    """
    Aikido's background process consists of 2 threads :
    - (main) Listening thread which listens on an IPC socket for incoming data
    - (spawned) reporting thread which collects IPC data and send it to a CloudConnectionManager
    """

    def __init__(self, address, key):
        logger.debug("Background process started")
        self.address = address
        try:
            listener = con.Listener(address, authkey=key)
        except OSError:
            logger.warning(
                "Aikido listener may already be running on port %s, exiting", address[1]
            )
            sys.exit(0)
        self.queue = Queue()
        self.connection_manager = None
        # Start reporting thread :
        Thread(target=self.reporting_thread).start()

        while True:
            conn = listener.accept()
            logger.debug("connection accepted from %s", listener.last_accepted)
            while True:
                try:
                    data = conn.recv()  #  because of this no sleep needed in thread
                    logger.debug("Incoming data : %s", data)
                    process_incoming_command(
                        connection_manager=self.connection_manager,
                        obj=data,
                        conn=conn,
                        queue=self.queue,
                    )
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
        self.send_to_connection_manager(event_scheduler)

        api = ReportingApiHTTPRatelimited(
            "https://guard.aikido.dev/",
            max_events_per_interval=100,
            interval_in_ms=60 * 60 * 1000,
        )
        # We need to pass along the scheduler so that the heartbeat also gets sent
        self.connection_manager = CloudConnectionManager(
            block=check_env_for_blocking(),
            api=api,
            token=get_token_from_env(),
            serverless=False,
        )
        time.sleep(2)  # Sleep 2 seconds to make sure modules get reported
        self.connection_manager.start(event_scheduler)

        self.socket_file_exists_check(event_scheduler)
        event_scheduler.run()

    def send_to_connection_manager(self, event_scheduler):
        """
        Reports the found data to an Aikido server
        """
        # Add back to event scheduler in EMPTY_QUEUE_INTERVAL secs :
        event_scheduler.enter(
            EMPTY_QUEUE_INTERVAL, 1, self.send_to_connection_manager, (event_scheduler,)
        )
        while not self.queue.empty():
            queue_attack_item = self.queue.get()
            self.connection_manager.on_detected_attack(
                attack=queue_attack_item[0],
                context=queue_attack_item[1],
                blocked=queue_attack_item[2],
                stack=queue_attack_item[3],
            )

    def socket_file_exists_check(self, event_scheduler):
        """Makes sure the socket file still exists"""
        # Every 60 seconds check if the socket file still exists
        event_scheduler.enter(60, 1, self.socket_file_exists_check, (event_scheduler,))
        if not os.path.exists(self.address):
            # Start termination process
            logger.info("Terminating a background process")
            os.kill()
