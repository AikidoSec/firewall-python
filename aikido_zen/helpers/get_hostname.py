"""
Helper function file, see function docstring
"""

import socket


def get_hostname():
    """Tries to fetch the hostname and returns an empty string on failure"""
    try:
        return socket.gethostname()
    except OSError:
        return ""
