"""Exports `process_statistics` function"""


def process_statistics(reporter, data, conn):
    """Changes statistics"""
    if not reporter or not reporter.statistics:
        return
    stats = reporter.statistics

    if data["action"] == "aborted_request":
        stats.requests["aborted"] += 1
    elif data["action"] == "request":
        stats.requests["total"] += 1
