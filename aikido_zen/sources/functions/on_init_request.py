from aikido_zen.context import Context
from aikido_zen.sources.functions.ip_allowed_to_access_route import (
    ip_allowed_to_access_route,
)
from aikido_zen.thread.thread_cache import get_cache


def on_init_request(context: Context):
    """
    This function gets the newly created context object and does the following :
    - Renews thread cache if necessary
    - Sets context object
    - Checks if the IP is allowed to access the route (route-specific)
    - Checks if the IP is in an allowlist (if that exists)
    - Checks if the IP is in a blocklist (if that exists)
    - Checks if the user agent is blocked (if the regex exists)
    """
    if not context:
        return False  # Early return
    context.set_as_current_context()  # Store context object

    # Refresh thread cache
    thread_cache = get_cache()
    if thread_cache:
        thread_cache.renew_if_ttl_expired()  # Only check TTL at the start of a request.
        thread_cache.increment_stats()  # Increment request statistics if a context exists.

    # Per endpoint IP Allowlist
    matched_endpoints = thread_cache.config.get_endpoints(context.get_route_metadata())
    if not ip_allowed_to_access_route(
        context.remote_address, context.get_route_metadata(), matched_endpoints
    ):
        message = "Your IP address is not allowed to access this resource."
        if context.remote_address:
            message += f" (Your IP: {context.remote_address})"
        return message, 403

    # Global IP Allowlist (e.g. for geofencing)
    if thread_cache.config.is_allowed_ip(context.remote_address):
        message = "Your IP address is not allowed."
        message += " (Your IP: " + context.remote_address + ")"
        return message, 403

    # Global IP Blocklist (e.g. blocking known threat actors)
    reason = thread_cache.config.is_blocked_ip(context.remote_address)
    if reason:
        message = "Your IP address is blocked due to " + reason
        message += " (Your IP: " + context.remote_address + ")"
        return message, 403

    # User agent blocking (e.g. blocking AI scrapers)
    if thread_cache.config.is_user_agent_blocked(context.headers["USER_AGENT"]):
        msg = "You are not allowed to access this resource because you have been identified as a bot."
        return msg, 403

    return False
