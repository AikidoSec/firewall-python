"""Exports `on_inspected_call`"""


def on_inspected_call(
    statistics_object, sink, duration_in_ms, attack_detected, blocked, without_context
):
    """Handle an inspected call and update statistics accordingly."""
    statistics_object.ensure_sink_stats(sink)

    statistics_object.stats[sink]["total"] += 1

    if without_context:
        statistics_object.stats[sink]["withoutContext"] += 1
        return

    if (
        len(statistics_object.stats[sink]["durations"])
        >= statistics_object.max_perf_samples_in_mem
    ):
        statistics_object.compress_perf_samples(sink)

    statistics_object.stats[sink]["durations"].append(duration_in_ms)

    if attack_detected:
        statistics_object.stats[sink]["attacksDetected"]["total"] += 1
        if blocked:
            statistics_object.stats[sink]["attacksDetected"]["blocked"] += 1
