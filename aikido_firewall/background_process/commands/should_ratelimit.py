"""Exports `process_should_ratelimit`"""

import aikido_firewall.ratelimiting as ratelimiting


def process_should_ratelimit(bg_process, data, conn):
    """
    Called to check if the context passed along as data should be rate limited
    data object should be a dict including route_metadata, remote_address and user
    route_metadata object includes route, url and method
    """
    should_ratelimit = ratelimiting.should_ratelimit_request(
        route_metadata=data["route_metadata"],
        remote_address=data["remote_address"],
        user=data["user"],
        reporter=bg_process.reporter,
    )
    conn.send(should_ratelimit)
