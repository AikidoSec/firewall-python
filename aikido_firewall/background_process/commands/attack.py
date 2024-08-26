"""Main export is process_attack"""


def process_attack(reporter, data, queue):
    """
    Adds ATTACK data object to queue
    Expected data object : [injection_results, context, blocked_or_not, stacktrace]
    """
    queue.put(data)
    if reporter and reporter.statistics:
        reporter.statistics.on_detected_attack(blocked=data[2])
