"""Exports request_handler function"""

import aikido_zen.context as ctx
from aikido_zen.api_discovery.get_api_info import get_api_info
from aikido_zen.api_discovery.update_route_info import update_route_info
from aikido_zen.helpers.is_useful_route import is_useful_route
from aikido_zen.helpers.logging import logger
from aikido_zen.thread.thread_cache import get_cache
from .ip_allowed_to_access_route import ip_allowed_to_access_route
from ...helpers.is_ip_allowed_by_allowlist import is_ip_allowed_by_allowlist


def request_handler(stage, status_code=0):
    """This will check for rate limiting, Allowed IP's, useful routes, etc."""
    try:
        if stage == "init":
            thread_cache = get_cache()
            if ctx.get_current_context() and thread_cache:
                thread_cache.increment_stats()  # Increment request statistics if a context exists.
        if stage == "pre_response":
            return pre_response()
        if stage == "post_response":
            return post_response(status_code)
    except Exception as e:
        logger.debug("Exception occurred in request_handler : %s", e)
    return None


def pre_response():
    """
    This is executed at the end of the middleware chain before a response is present
    - Checks if the IP is allowed to access the route (route-specific)
    - Checks if the IP is in an allowlist (if that exists)
    - Checks if the IP is in a blocklist (if that exists)
    - Checks if the user agent is blocked (if the regex exists)
    """
    context = ctx.get_current_context()
    cache = get_cache()
    if not context or not cache:
        logger.debug("Request was not complete, not running any pre_response code")
        return

    # Per endpoint IP Allowlist
    matched_endpoints = cache.config.get_endpoints(context.get_route_metadata())
    if not ip_allowed_to_access_route(
        context.remote_address, context.get_route_metadata(), matched_endpoints
    ):
        message = "Your IP address is not allowed to access this resource."
        if context.remote_address:
            message += f" (Your IP: {context.remote_address})"
        return message, 403

    # Global IP Allowlist (e.g. for geofencing)
    if not is_ip_allowed_by_allowlist(cache.config, context.remote_address):
        message = "Your IP address is not allowed."
        message += " (Your IP: " + context.remote_address + ")"
        return message, 403

    # Global IP Blocklist (e.g. blocking known threat actors)
    reason = cache.config.is_blocked_ip(context.remote_address)
    if reason:
        message = "Your IP address is blocked due to " + reason
        message += " (Your IP: " + context.remote_address + ")"
        return message, 403

    # User agent blocking (e.g. blocking AI scrapers)
    if cache.config.is_user_agent_blocked(context.get_user_agent()):
        msg = "You are not allowed to access this resource because you have been identified as a bot."
        return msg, 403


def post_response(status_code):
    """Checks if the current route is useful"""
    context = ctx.get_current_context()
    if not context:
        return
    route_metadata = context.get_route_metadata()

    is_curr_route_useful = is_useful_route(
        status_code,
        context.route,
        context.method,
    )
    if not is_curr_route_useful:
        return

    cache = get_cache()
    if cache:
        cache.routes.increment_route(route_metadata)

        # Run API Discovery :
        update_route_info(
            new_apispec=get_api_info(context), route=cache.routes.get(route_metadata)
        )
