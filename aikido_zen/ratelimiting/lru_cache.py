"""
Mainly exports the LRUCache class
"""

from collections import OrderedDict
from aikido_zen.helpers.get_current_unixtime_ms import get_unixtime_ms


class LRUCache:
    """Least Recently Used cache"""

    def __init__(self, max_items, time_to_live_in_ms):
        if max_items <= 0:
            raise ValueError("Invalid max value")
        if time_to_live_in_ms < 0:
            raise ValueError("Invalid ttl value")

        self.max_items = max_items
        self.time_to_live_in_ms = time_to_live_in_ms
        self.cache = OrderedDict()

    def get(self, key):
        """Get a value from the cache"""
        if key in self.cache:
            # Check if the item is still valid based on TTL
            if (
                get_unixtime_ms(monotonic=True) - self.cache[key]["startTime"]
                < self.time_to_live_in_ms
            ):
                return self.cache[key]["value"]  # Return the actual value
            else:
                # Remove expired item
                del self.cache[key]
        return None

    def set(self, key, value):
        """Set a value in the cache based on the key"""
        if key in self.cache:
            del self.cache[key]  # Remove the existing item
        elif len(self.cache) >= self.max_items:
            self.cache.popitem(last=False)  # Remove the oldest item
        self.cache[key] = {
            "value": value,
            "startTime": get_unixtime_ms(monotonic=True),
        }  # Store value and timestamp

    def clear(self):
        """Clear the cache entirely"""
        self.cache.clear()

    def delete(self, key):
        """Delete a cache item using the key as id"""
        if key in self.cache:
            del self.cache[key]

    def keys(self):
        """Get the keys in the cache"""
        return list(self.cache.keys())

    @property
    def size(self):
        """Get the size of the cache"""
        return len(self.cache)
