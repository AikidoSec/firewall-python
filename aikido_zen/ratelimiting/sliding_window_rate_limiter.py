"""
Mostly exports the class RateLimiter
"""

from typing import List
from aikido_zen.helpers.get_current_unixtime_ms import get_unixtime_ms
from .lru_cache import LRUCache
from .rate_limiter import RateLimiter


class SlidingWindowRateLimiter(RateLimiter):
    """Stores x times a request has been"""

    def __init__(self, max_items, time_to_live_in_ms):
        self.max_items = max_items
        self.time_to_live_in_ms = time_to_live_in_ms
        self.rate_limited_items = LRUCache(max_items, time_to_live_in_ms)

    def is_allowed(self, key, window_size_in_ms, max_requests):
        current_time = get_unixtime_ms()
        entries: SlidingWindowEntries = self.rate_limited_items.get(key)

        if entries is None:
            entries = SlidingWindowEntries(window_size_in_ms, max_requests)
            self.rate_limited_items.set(key, entries)

        entries.add_hit(current_time)  # Adds hit
        return entries.get_hits_in_window(current_time) <= max_requests


class SlidingWindowEntries:
    """
    Holds timestamps for requests made to the owner of this object.
    This class implements a sliding window mechanism to track request timestamps
    and manage rate limiting based on a specified time window.
    """

    def __init__(self, window_size_ms: int, max_requests: int) -> None:
        """Initializes with a specified time window and maximum requests."""
        self.entries: List[int] = (
            []
        )  # List to hold UNIX timestamps (in milliseconds) of all requests.
        self.window_size_ms: int = window_size_ms  # Time window size in milliseconds.
        self.max_requests: int = max_requests  # Maximum number of requests allowed.

    def add_hit(self, current_time: int) -> None:
        """Adds a new request timestamp to the entries."""
        self.entries.append(current_time)

    def get_hits_in_window(self, current_time: int) -> int:
        """Returns the number of requests made within the current time window."""
        self.clear_entries(current_time)  # Clear old entries outside the time window.
        return len(
            self.entries
        )  # Returns the count of entries within the current time window.

    def clear_entries(self, current_time: int) -> None:
        """Removes entries that are older than the specified time window."""
        threshold_time = (
            current_time - self.window_size_ms
        )  # Calculate the threshold time.
        self.entries = [
            entry for entry in self.entries if entry >= threshold_time
        ]  # Remove old entries.

        # Ensure the number of entries does not exceed max_requests by only 1
        while len(self.entries) > (self.max_requests + 1):
            self.entries.pop(0)  # Remove the oldest entry.
