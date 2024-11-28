"""Mainly exports check_if_ip_blocked"""

from aikido_zen.context import get_current_context
from aikido_zen.sources.functions.ip_allowed_to_access_route import (
    ip_allowed_to_access_route,
)


def check_if_ip_blocked(context, endpoints):
    """
    Inspects the IP address of the request:
    - Whether the IP address is blocked by an IP blocklist (e.g. Geo restrictions)
    - Whether the IP address is allowed to access the current route (e.g. Admin panel)
    """
    if not context:
        return False

    # Whether the IP address is blocked by an IP blocklist (e.g. Geo restrictions)
    # NOP

    # Whether the IP address is allowed to access the current route (e.g. Admin panel)
    ip_allowed_access = ip_allowed_to_access_route(
        context.remote_address, context.get_route_metadata(), endpoints
    )
    if not ip_allowed_access:
        message = "Your IP address is not allowed to access this resource."
        if context.remote_address:
            message += f" (Your IP: {context.remote_address})"
        return message, 403

    return False
