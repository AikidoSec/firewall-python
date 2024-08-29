"""Exports `process_statistics` function"""


def process_statistics(connection_manager, data, queue=None):
    """Changes statistics"""
    if not connection_manager or not connection_manager.statistics:
        return
    stats = connection_manager.statistics

    if data["action"] == "aborted_request":
        stats.requests["aborted"] += 1
    elif data["action"] == "request":
        stats.requests["total"] += 1
