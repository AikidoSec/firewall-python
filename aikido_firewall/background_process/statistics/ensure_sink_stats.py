"""Exports ensure_sink_stats function"""

import copy

EMPTY_STATS_OBJECT = {
    "withoutContext": 0,
    "total": 0,
    "durations": [],
    "compressedTimings": [],
    "interceptorThrewError": 0,
    "attacksDetected": {
        "total": 0,
        "blocked": 0,
    },
}


def ensure_sink_stats(statistics_obj, sink):
    """Makes sure to initalize sink if it's not there"""
    if sink not in statistics_obj.stats:
        statistics_obj.stats[sink] = copy.deepcopy(EMPTY_STATS_OBJECT)
