"""Exports statistics class"""

from aikido_zen.helpers.get_current_unixtime_ms import get_unixtime_ms
from .ensure_sink_stats import ensure_sink_stats
from .compress_perf_samples import compress_perf_samples
from .on_inspected_call import on_inspected_call
from .get_stats import get_stats


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
        self.stats = {}
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

    def interceptor_threw_error(self, sink):
        """Increment the error count for the interceptor for the given sink."""
        self.ensure_sink_stats(sink)
        self.stats[sink]["total"] += 1
        self.stats[sink]["interceptorThrewError"] += 1

    def on_detected_attack(self, blocked):
        """Increment the attack detection statistics."""
        self.requests["attacksDetected"]["total"] += 1
        if blocked:
            self.requests["attacksDetected"]["blocked"] += 1

    def force_compress(self):
        """Force compression of performance samples for all sinks."""
        for sink in self.stats:
            self.compress_perf_samples(sink)

    def ensure_sink_stats(self, sink):
        """Makes sure to initalize sink if it's not there"""
        return ensure_sink_stats(self, sink)

    def compress_perf_samples(self, sink):
        """Compress performance samples for a given sink."""
        return compress_perf_samples(self, sink)

    def on_inspected_call(self, *args, **kwargs):
        """Handle an inspected call and update statistics accordingly."""
        return on_inspected_call(self, *args, **kwargs)

    def get_stats(self):
        """This will return the stats as a dict, from a Statistics class"""
        return get_stats(self)

    def is_empty(self):
        """This will return a boolean value indicating if the stats are empty"""
        return (
            len(self.stats) == 0
            and self.requests["total"] == 0
            and self.requests["attacksDetected"]["total"] == 0
        )
