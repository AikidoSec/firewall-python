"""Main export is process_attack"""


def process_attack(connection_manager, data, queue):
    """
    Adds ATTACK data object to queue
    Expected data object : [injection_results, context, blocked_or_not, stacktrace]
    """
    queue.put(data)
