"""Main export is process_attack"""


def process_attack(bg_process, data, conn):
    """Adds ATTACK data object to queue"""
    bg_process.queue.put(data)
    if bg_process.reporter.statistics:
        bg_process.reporter.statistics.on_detected_attack(blocked=data[2])
