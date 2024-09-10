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
        request_info = self.rate_limited_items.get(key)

        if request_info is None:
            self.rate_limited_items.set(key, {"count": 1, "startTime": current_time})
            return True

        elapsed_time = current_time - request_info["startTime"]

        if elapsed_time > window_size_in_ms:
            # Reset the counter and timestamp if windowSizeInMS has expired
            self.rate_limited_items.set(key, {"count": 1, "startTime": current_time})
            return True

        if request_info["count"] < max_requests:
            # Increment the counter if it is within the windowSizeInMS and maxRequests
            request_info["count"] += 1
            self.rate_limited_items.set(key, request_info)  # Update the cache
            return True

        # Deny the request if the maxRequests is reached within windowSizeInMS
        return False
