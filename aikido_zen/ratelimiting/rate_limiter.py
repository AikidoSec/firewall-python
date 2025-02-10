"""
Mostly exports the class RateLimiter
"""

from abc import ABC, abstractmethod


class RateLimiter(ABC):
    """Rate Limiter interface"""

    @abstractmethod
    def is_allowed(self, key, window_size_in_ms, max_requests):
        """
        Checks if the request is allowed given the history
        """

        pass
