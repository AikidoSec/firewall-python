"""
Helper function file, see function docstring
"""

import socket
from functools import lru_cache


@lru_cache(maxsize=1)
def get_ip():
    """Tries to fetch the IP and returns x.x.x.x on failure"""
    # Cached: this queries DNS and runs on every report.
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:  # pylint: disable=broad-exception-caught
        return "x.x.x.x"
