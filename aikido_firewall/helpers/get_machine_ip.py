"""
Helper function file, see function docstring
"""

import socket


def get_ip():
    """Tries to fetch the IP and returns x.x.x.x on failure"""
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return "x.x.x.x"
