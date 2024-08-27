"""Main export is process_attack"""


def process_attack(connection_manager, data, queue):
    """
    Adds ATTACK data object to queue
    Expected data object : [injection_results, context, blocked_or_not, stacktrace]
    """
    if queue:
        queue.put(data)
    else:
        connection_manager.on_detected_attack(
            attack=data[0], context=data[1], blocked=data[2], stack=data[3]
        )
    if connection_manager and connection_manager.statistics:
        connection_manager.statistics.on_detected_attack(blocked=data[2])
