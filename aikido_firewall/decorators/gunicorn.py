"""
Includes all the wrappers for gunicorn config file
"""

import atexit
import aikido_firewall
from aikido_firewall.background_process import get_comms
from aikido_firewall.helpers.logging import logger


def when_ready(prev_func):
    """
    Aikido decorator for gunicorn config
    Function: pre_request(worker, req)
    """

    def aik_when_ready(server):
        prev_func(server)

    return aik_when_ready


def post_fork(prev_func):
    """
    Aikido decorator for gunicorn config
    Function: post_fork(server, worker)
    """

    def aik_post_fork(server, worker):
        aikido_firewall.protect()
        prev_func(server, worker)

    return aik_post_fork
