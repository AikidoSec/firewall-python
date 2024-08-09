"""Main export is process_attack"""


def process_attack(bg_process, data):
    """Adds ATTACK data object to queue"""
    bg_process.queue.put(data)
