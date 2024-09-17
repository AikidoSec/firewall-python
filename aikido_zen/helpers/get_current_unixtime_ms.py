"""
Helper function file, see function docstring
"""

import time


def get_unixtime_ms(monotonic=False):
    """Get the current unix time but in ms"""
    if monotonic:
        # Return monotonic time, used for intervals.
        return int(time.monotonic() * 1000)
    return int(time.time() * 1000)
