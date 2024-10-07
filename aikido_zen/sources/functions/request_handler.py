"""Exports request_handler function"""

from aikido_zen.background_process import get_comms
from aikido_zen.context import get_current_context
from aikido_zen.api_discovery.get_api_info import get_api_info
from aikido_zen.api_discovery.update_route_info import ANALYSIS_ON_FIRST_X_ROUTES
from aikido_zen.helpers.is_useful_route import is_useful_route
from aikido_zen.helpers.logging import logger
from aikido_zen.thread.thread_cache import get_cache
from aikido_zen.ratelimiting.get_ratelimited_endpoint import get_ratelimited_endpoint
from .ip_allowed_to_access_route import ip_allowed_to_access_route
from aikido_zen.helpers.match_endpoints import match_endpoints


def request_handler(stage, status_code=0):
    """This will check for rate limiting, Allowed IP's, useful routes, etc."""
    try:
        if stage == "init":
            #  This gets executed the first time a request get's intercepted
            context = get_current_context()
            thread_cache = get_cache()
            if context and thread_cache:
                # Increment the route hits if the route exists :
                thread_cache.routes.increment_route(context.get_route_metadata())

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
    context = get_current_context()
    comms = get_comms()
    if not context or not comms:
        logger.debug("Request was not complete, not running any pre_response code")
        return

    # Blocked users:
    if context.user:
        blocked_res = comms.send_data_to_bg_process(
            action="SHOULD_BLOCK_USER", obj=context.user["id"], receive=True
        )
        if blocked_res["success"] and blocked_res["data"]:
            return ("You are blocked by Aikido Firewall.", 403)

    # Fetch endpoints for IP Allowlist and ratelimiting :
    route_metadata = context.get_route_metadata()
    endpoints = getattr(get_cache(), "endpoints", None)
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
    context = get_current_context()
    comms = get_comms()
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
    route = get_cache().routes.get(route_metadata)
    if not route:
        # This route does not exist yet, initialize it:
        get_cache().routes.initialize_route(route_metadata)
    elif route["hits"] < ANALYSIS_ON_FIRST_X_ROUTES:
        # Only analyze the first x routes for api discovery
        apispec = get_api_info(context)
        if not apispec:
            return
        get_comms().send_data_to_bg_process(
            "UPDATE_APISPEC", {"route_metadata": route_metadata, "apispec": apispec}
        )
