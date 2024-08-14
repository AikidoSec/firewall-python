"""Mainly exports `process_is_bypassed_ip`"""


def process_is_bypassed_ip(bg_process, data, conn):
    """Checks if the ip is on the bypass list"""
    is_bypassed = bg_process.reporter.conf.is_bypassed_ip(data)
    conn.send(is_bypassed)
