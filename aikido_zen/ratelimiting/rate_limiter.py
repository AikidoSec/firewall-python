"""
Mostly exports the class RateLimiter
"""

from aikido_zen.helpers.get_current_unixtime_ms import get_unixtime_ms
from .lru_cache import LRUCache


class RateLimiter:
    """
    Stores x times a request has been
    """

    def __init__(self, max_items, time_to_live_in_ms):
        self.max_items = max_items
        self.time_to_live_in_ms = time_to_live_in_ms
        self.rate_limited_items = LRUCache(max_items, time_to_live_in_ms)

    def record_request(self, key, window_size_in_ms, max_requests):
        """
        Records a request for this key and checks it against the limit.
        Returns {"allowed": True}, or {"allowed": False, "retry_after_seconds": n},
        where n is None when no retry can succeed.
        """
        # Core accepts a maxRequests below 1, which blocks every request forever.
        if max_requests < 1:
            return {"allowed": False, "retry_after_seconds": None}

        current_time = get_unixtime_ms()
        request_timestamps = self.rate_limited_items.get(key) or []

        # clear entries that are not in the rate-limiting window anymore
        request_timestamps = [
            timestamp
            for timestamp in request_timestamps
            if timestamp >= current_time - window_size_in_ms
        ]

        # ensure the number of entries exceeds max_requests by only 1
        while len(request_timestamps) > (max_requests + 1):
            # We remove the oldest entry, since this one has become useless if the limit is already exceeded
            request_timestamps.pop(0)  # Remove the first element

        # update entries by adding the new timestamp and storing it in the LRU Cache
        request_timestamps.append(current_time)
        self.rate_limited_items.set(key, request_timestamps)

        # if the total amount of requests in the current window exceeds max requests, we rate-limit
        if len(request_timestamps) <= max_requests:
            return {"allowed": True}

        # Blocked requests are stored too: wait for this one to leave, not the oldest.
        blocking_timestamp = request_timestamps[-max_requests]

        # A timestamp exactly one window old still counts, so the wait must be longer.
        retry_after_ms = blocking_timestamp + window_size_in_ms - current_time
        return {"allowed": False, "retry_after_seconds": retry_after_ms // 1000 + 1}
