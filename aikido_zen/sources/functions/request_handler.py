"""Exports request_handler function"""

import aikido_zen.background_process as communications
import aikido_zen.context as ctx
from aikido_zen.api_discovery.get_api_info import get_api_info
from aikido_zen.api_discovery.update_route_info import update_route_info
from aikido_zen.helpers.is_useful_route import is_useful_route
from aikido_zen.helpers.logging import logger
from aikido_zen.thread.thread_cache import get_cache
from aikido_zen.ratelimiting.get_ratelimited_endpoint import get_ratelimited_endpoint
from aikido_zen.helpers.match_endpoints import match_endpoints
from .check_if_ip_blocked import check_if_ip_blocked
from .ip_allowed_to_access_route import ip_allowed_to_access_route


def request_handler(stage, status_code=0):
    """This will check for rate limiting, Allowed IP's, useful routes, etc."""
    try:
        if stage == "init":
            # Initial stage of the request, called after context is stored.
            thread_cache = get_cache()
            thread_cache.renew_if_ttl_expired()  # Only check TTL at the start of a request.
            if ctx.get_current_context() and thread_cache:
                thread_cache.increment_stats()  # Increment request statistics if a context exists.

        if stage == "pre_response":
            return pre_response()
        if stage == "post_response":
            return post_response(status_code)
    except Exception as e:
        logger.debug("Exception occured in request_handler : %s", e)
    return None


def pre_response():
    """
    This is executed at the end of the middleware chain before a response is present
    - IP Allowlist
    """
    context = ctx.get_current_context()
    comms = communications.get_comms()
    if not context or not comms:
        logger.debug("Request was not complete, not running any pre_response code")
        return

    # Fetch endpoints for IP Allowlist :
    route_metadata = context.get_route_metadata()
    endpoints = get_cache().get_endpoints()

    # IP Allowlist/Blocklist:
    ip_check_result = check_if_ip_blocked(context, endpoints, get_cache().config)
    if ip_check_result:
        return ip_check_result


def post_response(status_code):
    """Checks if the current route is useful"""
    context = ctx.get_current_context()
    comms = communications.get_comms()
    if not context or not comms:
        return
    is_curr_route_useful = is_useful_route(
        status_code,
        context.route,
        context.method,
    )
    if not is_curr_route_useful:
        return
    route_metadata = context.get_route_metadata()
    cache = get_cache()
    if cache:
        route = cache.routes.get(route_metadata)
        if not route:
            # This route does not exist yet, initialize it:
            cache.routes.initialize_route(route_metadata)
            comms.send_data_to_bg_process("INITIALIZE_ROUTE", route_metadata)
        # Run API Discovery :
        update_route_info(
            new_apispec=get_api_info(context), route=cache.routes.get(route_metadata)
        )
        # Add hit :
        cache.routes.increment_route(route_metadata)
