"""
Helper function file, see function docstring
"""

import socket
from functools import lru_cache


@lru_cache(maxsize=1)
def get_hostname():
    """Tries to fetch the hostname and returns an empty string on failure"""
    try:
        return socket.gethostname()
    except OSError:
        return ""
