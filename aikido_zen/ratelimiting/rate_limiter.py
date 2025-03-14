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

    def is_allowed(self, key, window_size_in_ms, max_requests):
        """
        Checks if the request is allowed given the history
        """
        current_time = get_unixtime_ms()
        request_timestamps = self.rate_limited_items.get(key) or list()

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
        return len(request_timestamps) <= max_requests
