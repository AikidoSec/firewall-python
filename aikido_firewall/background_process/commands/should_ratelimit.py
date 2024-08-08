"""Exports `process_should_ratelimit`"""

from aikido_firewall.ratelimiting import should_ratelimit_request


def process_should_ratelimit(bg_process, data, conn):
    """
    Called to check if the context passed along as data should be rate limited
    """
    conn.send(should_ratelimit_request(context=data, reporter=bg_process.reporter))
