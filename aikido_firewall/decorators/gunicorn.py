"""
Includes all the wrappers for gunicorn config file
"""

import signal
import aikido_firewall
from aikido_firewall.background_process import get_comms
from aikido_firewall.helpers.logging import logger


def signal_handler(sig, frame):
    """Signal handler on SIGTERM/SIGKILL"""
    logger.critical("Killing background process... (Received SIGINT/SIGTERM)")
    get_comms().send_data_to_bg_process("KILL", None)


def when_ready(prev_func):
    """
    Aikido decorator for gunicorn config
    Function: pre_request(worker, req)
    """

    def aik_when_ready(server):
        signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Handle termination signal

        aikido_firewall.protect("background-process-only")
        prev_func(server)

    return aik_when_ready


def post_fork(prev_func):
    """
    Aikido decorator for gunicorn config
    Function: post_fork(server, worker)
    """

    def aik_post_fork(server, worker):
        aikido_firewall.protect(server=False)
        prev_func(server, worker)

    return aik_post_fork
