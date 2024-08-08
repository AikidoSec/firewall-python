"""Exports `process_should_ratelimit`"""

import aikido_firewall.ratelimiting as ratelimiting


def process_should_ratelimit(bg_process, data, conn):
    """
    Called to check if the context passed along as data should be rate limited
    """
    should_ratelimit = ratelimiting.should_ratelimit_request(
        context=data, reporter=bg_process.reporter
    )
    conn.send(should_ratelimit)
