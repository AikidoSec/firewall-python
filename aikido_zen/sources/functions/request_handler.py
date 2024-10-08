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
from .ip_allowed_to_access_route import ip_allowed_to_access_route


def request_handler(stage, status_code=0):
    """This will check for rate limiting, Allowed IP's, useful routes, etc."""
    try:
        if stage == "init":
            #  This gets executed the first time a request get's intercepted
            context = ctx.get_current_context()
            thread_cache = get_cache()
            if context and thread_cache:
                thread_cache.increment_stats()  # Increment request statistics

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
    - Blocked users
    - Ratelimiting
    """
    context = ctx.get_current_context()
    comms = communications.get_comms()
    if not context or not comms:
        logger.debug("Request was not complete, not running any pre_response code")
        return

    # Blocked users:
    if context.user and get_cache() and get_cache().is_user_blocked(context.user["id"]):
        return ("You are blocked by Aikido Firewall.", 403)

    # Fetch endpoints for IP Allowlist and ratelimiting :
    route_metadata = context.get_route_metadata()
    endpoints = getattr(get_cache(), "endpoints", None)
    if not endpoints:
        return
    matched_endpoints = match_endpoints(route_metadata, endpoints)
    if not matched_endpoints:
        return

    # IP Allowlist:
    if not ip_allowed_to_access_route(
        context.remote_address, route_metadata, matched_endpoints
    ):
        message = "Your IP address is not allowed to access this resource."
        if context.remote_address:
            message += f" (Your IP: {context.remote_address})"
        return (message, 403)

    # Ratelimiting :
    if get_ratelimited_endpoint(matched_endpoints, context.route):
        # As an optimization check if the route is rate limited before sending over IPC
        ratelimit_res = comms.send_data_to_bg_process(
            action="SHOULD_RATELIMIT",
            obj={
                "route_metadata": route_metadata,
                "user": context.user,
                "remote_address": context.remote_address,
            },
            receive=True,
        )
        if ratelimit_res["success"] and ratelimit_res["data"]["block"]:
            message = "You are rate limited by Zen"
            if ratelimit_res["data"]["trigger"] == "ip":
                message += f" (Your IP: {context.remote_address})"
            return (message, 429)


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
