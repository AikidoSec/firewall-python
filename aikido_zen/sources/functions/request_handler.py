"""Exports request_handler function"""

from aikido_zen.background_process import get_comms
from aikido_zen.context import get_current_context
from aikido_zen.api_discovery.get_api_info import get_api_info
from aikido_zen.api_discovery.update_route_info import ANALYSIS_ON_FIRST_X_ROUTES
from aikido_zen.helpers.is_useful_route import is_useful_route
from aikido_zen.helpers.logging import logger
from aikido_zen.background_process.ipc_lifecycle_cache import (
    IPCLifecycleCache,
    get_cache,
)
from aikido_zen.ratelimiting.get_ratelimited_endpoint import get_ratelimited_endpoint
from .ip_allowed_to_access_route import ip_allowed_to_access_route


def request_handler(stage, status_code=0):
    """This will check for rate limiting, Allowed IP's, useful routes, etc."""
    try:
        if stage == "init":
            #  This gets executed the first time a request get's intercepted
            context = get_current_context()
            if context:  # Create a lifecycle cache
                # This fetches initial metadata, which also adds statistics
                # and increments this route's hits. (Optimization)
                IPCLifecycleCache(context)
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
    endpoints = getattr(get_cache(), "matched_endpoints", None)
    if not endpoints:
        return

    # IP Allowlist:
    if not ip_allowed_to_access_route(
        context.remote_address, context.get_route_metadata(), endpoints
    ):
        message = "Your IP address is not allowed to access this resource."
        if context.remote_address:
            message += f" (Your IP: {context.remote_address})"
        return (message, 403)

    # Ratelimiting :
    if get_ratelimited_endpoint(endpoints, context.route):
        # As an optimization check if the route is rate limited before sending over IPC
        ratelimit_res = comms.send_data_to_bg_process(
            action="SHOULD_RATELIMIT",
            obj={
                "route_metadata": context.get_route_metadata(),
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
    hits = getattr(get_cache(), "hits", 0)
    route_metadata = context.get_route_metadata()
    if hits == 0:
        # This route does not exist yet, initialize it:
        get_comms().send_data_to_bg_process("INITIALIZE_ROUTE", route_metadata)
    if hits < ANALYSIS_ON_FIRST_X_ROUTES:
        # Only analyze the first x routes for api discovery
        apispec = get_api_info(context)
        if not apispec:
            return
        get_comms().send_data_to_bg_process(
            "UPDATE_APISPEC", {"route_metadata": route_metadata, "apispec": apispec}
        )
