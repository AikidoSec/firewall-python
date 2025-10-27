from unittest.mock import patch


def patch_time(monotonic=False, time_s=None, time_ms=None):
    if time_s is None and time_ms is None:
        raise ValueError("Time must be provided, either in seconds or in milliseconds.")
    if time_s is None:
        time_s = time_ms / 1000
    if monotonic:
        return patch("time.monotonic", return_value=time_s)
    else:
        return patch("time.time", return_value=time_s)
