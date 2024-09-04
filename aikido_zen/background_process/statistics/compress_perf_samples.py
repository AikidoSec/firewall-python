"""Exports `compress_perf_samples` function"""

from aikido_zen.helpers.percentiles import percentiles
from aikido_zen.helpers.get_current_unixtime_ms import get_unixtime_ms


def compress_perf_samples(statistics_object, sink):
    """Compress performance samples for a given sink."""
    # Ignore if sink stats do not exist or if there are no durations
    if (
        sink not in statistics_object.stats
        or not statistics_object.stats[sink]["durations"]
    ):
        return

    timings = statistics_object.stats[sink]["durations"]
    average_in_ms = sum(timings) / len(timings)

    p50, p75, p90, p95, p99 = percentiles([50, 75, 90, 95, 99], timings)

    statistics_object.stats[sink]["compressedTimings"].append(
        {
            "averageInMS": average_in_ms,
            "percentiles": {
                "50": p50,
                "75": p75,
                "90": p90,
                "95": p95,
                "99": p99,
            },
            "compressedAt": get_unixtime_ms(),
        }
    )

    # Remove the oldest compressed timing if exceeding the limit
    if (
        len(statistics_object.stats[sink]["compressedTimings"])
        > statistics_object.max_compressed_stats_in_mem
    ):
        statistics_object.stats[sink]["compressedTimings"].pop(0)

    # Clear the durations
    statistics_object.stats[sink]["durations"] = []
