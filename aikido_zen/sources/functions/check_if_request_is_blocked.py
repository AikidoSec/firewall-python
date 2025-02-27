"""Mainly exports check_if_ip_blocked"""

from aikido_zen.context import get_current_context, Context
from aikido_zen.sources.functions.ip_allowed_to_access_route import (
    ip_allowed_to_access_route,
)
from aikido_zen.thread.thread_cache import get_cache


class BlockResult:
    def __init__(self, blocking=False, message="", status_code=403):
        self.blocking = blocking
        self.message = message
        self.status_code = status_code


def check_if_request_is_blocked(context: Context) -> BlockResult:
    """
    - Checks if the IP is allowed to access the route (route-specific)
    - Checks if the IP is in a blocklist (if that exists)
    """
    if context is None:
        return BlockResult(False)
    cache = get_cache()
    if cache is None:
        return BlockResult(False)

    # Per endpoint IP Allowlist
    matched_endpoints = cache.config.get_endpoints(context.get_route_metadata())
    if not ip_allowed_to_access_route(
        context.remote_address, context.get_route_metadata(), matched_endpoints
    ):
        message = "Your IP address is not allowed to access this resource."
        if context.remote_address:
            message += f" (Your IP: {context.remote_address})"
        return BlockResult(True, message)

    # Global IP Blocklist (e.g. blocking known threat actors)
    reason = cache.config.is_blocked_ip(context.remote_address)
    if reason:
        message = "Your IP address is blocked due to " + reason
        message += " (Your IP: " + context.remote_address + ")"
        return BlockResult(True, message)

    return BlockResult(False)
