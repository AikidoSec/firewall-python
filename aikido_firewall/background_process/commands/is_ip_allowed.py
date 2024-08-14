"""Exports `process_is_ip_allowed`"""

from aikido_firewall.sources.functions.ip_allowed_to_access_route import (
    ip_allowed_to_access_route,
)


def process_is_ip_allowed(bg_process, data, conn):
    """Checks if the IP is allowed to access the route"""
    res = ip_allowed_to_access_route(context=data[0], reporter=bg_process.reporter)
    conn.send(res)
