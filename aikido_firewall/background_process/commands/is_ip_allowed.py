"""Exports `process_is_ip_allowed`"""

from aikido_firewall.sources.functions.ip_allowed_to_access_route import (
    ip_allowed_to_access_route,
)


def process_is_ip_allowed(reporter, data, conn, queue=None):
    """Checks if the IP is allowed to access the route"""
    if not reporter:
        return conn.send(True)
    route_metadata = data["route_metadata"]
    remote_address = data["remote_address"]
    res = ip_allowed_to_access_route(remote_address, route_metadata, reporter)
    conn.send(res)
