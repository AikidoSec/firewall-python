"""Exports get_stats function"""

import aikido_zen.helpers.get_current_unixtime_ms as t


def get_stats(statistics_object):
    """This will return the stats as a dict, from a Statistics class"""
    sinks = {}
    for sink, sink_stats in statistics_object.stats.items():
        sinks[sink] = {
            "total": sink_stats["total"],
            "attacksDetected": {
                "total": sink_stats["attacksDetected"]["total"],
                "blocked": sink_stats["attacksDetected"]["blocked"],
            },
            "interceptorThrewError": sink_stats["interceptorThrewError"],
            "withoutContext": sink_stats["withoutContext"],
            "compressedTimings": sink_stats["compressedTimings"],
        }

    return {
        "sinks": sinks,
        "startedAt": statistics_object.started_at,
        "endedAt": t.get_unixtime_ms(),
        "requests": statistics_object.requests,
    }
