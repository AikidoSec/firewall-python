"""Exports `process_is_ip_allowed`"""

from aikido_zen.sources.functions.ip_allowed_to_access_route import (
    ip_allowed_to_access_route,
)


def process_is_ip_allowed(connection_manager, data, queue=None):
    """Checks if the IP is allowed to access the route"""
    if not connection_manager:
        return True
    route_metadata = data["route_metadata"]
    remote_address = data["remote_address"]
    return ip_allowed_to_access_route(
        remote_address, route_metadata, connection_manager
    )
