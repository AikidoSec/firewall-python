"""
Helper function file, see function docstring
"""

import time


def get_unixtime_ms():
    """Get the current unix time but in ms"""
    return int(time.time() * 1000)
