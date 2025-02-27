from aikido_zen.context import Context
from aikido_zen.helpers.is_ip_allowed_by_allowlist import is_ip_allowed_by_allowlist
from aikido_zen.sources.functions.ip_allowed_to_access_route import (
    ip_allowed_to_access_route,
)
from aikido_zen.thread.thread_cache import get_cache


def on_init_handler(context: Context):
    """
    On-Init Handler should be called after a context has been created, the function will :
    - Store context
    - Renew thread cache if necessary and store the hits
    - Checks if the IP is allowed to access the route (route-specific)
    - Checks if the IP is in an allowlist (if that exists)
    - Checks if the IP is in a blocklist (if that exists)
    - Checks if the user agent is blocked (if the regex exists)
    """
    if context is None:
        return BlockResult(False)
    context.set_as_current_context()  # Save the new context

    # Checking TTL and Hit Statistics
    cache = get_cache()
    if cache is None:
        return BlockResult(False)
    cache.renew_if_ttl_expired()  # Only check TTL at the start of a request.
    cache.increment_stats()

    # Per endpoint IP Allowlist
    matched_endpoints = cache.config.get_endpoints(context.get_route_metadata())
    if not ip_allowed_to_access_route(
        context.remote_address, context.get_route_metadata(), matched_endpoints
    ):
        message = "Your IP address is not allowed to access this resource."
        if context.remote_address:
            message += f" (Your IP: {context.remote_address})"
        return BlockResult(True, message)

    # Global IP Allowlist (e.g. for geofencing)
    if not is_ip_allowed_by_allowlist(cache.config, context.remote_address):
        message = "Your IP address is not allowed."
        message += " (Your IP: " + context.remote_address + ")"
        return BlockResult(True, message)

    # Global IP Blocklist (e.g. blocking known threat actors)
    reason = cache.config.is_blocked_ip(context.remote_address)
    if reason:
        message = "Your IP address is blocked due to " + reason
        message += " (Your IP: " + context.remote_address + ")"
        return BlockResult(True, message)

    # User agent blocking (e.g. blocking AI scrapers)
    if cache.config.is_user_agent_blocked(context.get_user_agent()):
        msg = "You are not allowed to access this resource because you have been identified as a bot."
        return BlockResult(True, msg)

    return BlockResult(False)


class BlockResult:
    def __init__(self, blocking=False, message="", status_code=403):
        self.blocking = blocking
        self.message = message
        self.status_code = status_code
