"""Exports `process_statistics` function"""


def process_statistics(bg_process, data, conn):
    """Changes statistics"""
    stats = bg_process.reporter.statistics
    if not stats:
        return
    if data["action"] == "aborted_request":
        stats.requests["aborted"] += 1
    elif data["action"] == "request":
        stats.requests["total"] += 1
