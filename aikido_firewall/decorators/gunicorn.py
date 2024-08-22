"""
Includes all the wrappers for gunicorn config file
"""

import atexit
import aikido_firewall
from aikido_firewall.background_process import get_comms
from aikido_firewall.helpers.logging import logger


def signal_handler():
    """Signal handler on SIGTERM/SIGKILL"""
    try:
        logger.info("Killing background process... (Received SIGINT/SIGTERM)")
        get_comms().background_process.terminate()
    except Exception:
        pass


atexit.register(signal_handler)


def when_ready(prev_func):
    """
    Aikido decorator for gunicorn config
    Function: pre_request(worker, req)
    """

    def aik_when_ready(server):
        atexit.register(signal_handler)

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
