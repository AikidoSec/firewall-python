"""Exports statistics class"""

from aikido_firewall.helpers.get_current_unixtime_ms import get_unixtime_ms


class Statistics:
    """
    Keeps track of total and aborted requests
    and total and blocked attacks
    """

    def __init__(self, max_perf_samples_in_mem, max_compressed_stats_in_mem):
        self.max_perf_samples_in_mem = max_perf_samples_in_mem
        self.max_compressed_stats_in_mem = max_compressed_stats_in_mem
        self.reset()

    def reset(self):
        """Resets the stored data to an initial state"""
        self.stats = dict()
        self.requests = {
            "total": 0,
            "aborted": 0,
            "attacksDetected": {
                "total": 0,
                "blocked": 0,
            },
        }
        self.started_at = get_unixtime_ms()

    def has_compressed_stats(self):
        """Checks if there are any compressed statistics"""
        return any(
            len(sink_stats["compressedTimings"]) > 0
            for sink_stats in self.stats.values()
        )
