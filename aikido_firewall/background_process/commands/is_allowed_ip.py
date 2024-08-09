"""Mainly exports `process_is_allowed_ip`"""


def process_is_allowed_ip(bg_process, data, conn):
    """Checks if the ip is on a whitelist"""
    is_allowed = bg_process.reporter.conf.is_allowed_ip(data)
    conn.send(is_allowed)
