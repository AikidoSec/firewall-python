"""Exports `process_is_ip_allowed`"""

from aikido_firewall.sources.functions.ip_allowed_to_access_route import (
    ip_allowed_to_access_route,
)


def process_is_ip_allowed(bg_process, data, conn):
    """Checks if the IP is allowed to access the route"""
    context_metadata = data["context_metadata"]
    remote_address = data["remote_address"]
    res = ip_allowed_to_access_route(
        remote_address, context_metadata, reporter=bg_process.reporter
    )
    conn.send(res)
