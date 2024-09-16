"""Exports request_handler function"""

from aikido_zen.background_process import get_comms
from aikido_zen.context import get_current_context
from aikido_zen.helpers.is_useful_route import is_useful_route
from aikido_zen.helpers.logging import logger
from aikido_zen.background_process.ipc_lifecycle_cache import (
    IPCLifecycleCache,
)


def request_handler(stage, status_code=0):
    """This will check for rate limiting, Allowed IP's, useful routes, etc."""
    try:
        if stage == "init":
            #  This gets executed the first time a request get's intercepted
            if get_comms():
                get_comms().send_data_to_bg_process("STATISTICS", {"action": "request"})
            context = get_current_context()
            if context:  # Create a lifecycle cache
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

    # IP Allowlist:
    res = comms.send_data_to_bg_process(
        action="IS_IP_ALLOWED",
        obj={
            "route_metadata": context.get_route_metadata(),
            "remote_address": context.remote_address,
        },
        receive=True,
    )
    if res["success"] and not res["data"]:
        message = "Your IP address is not allowed to access this resource."
        if context.remote_address:
            message += f" (Your IP: {context.remote_address})"
        return (message, 403)

    # Blocked users:
    if context.user:
        blocked_res = comms.send_data_to_bg_process(
            action="SHOULD_BLOCK_USER", obj=context.user["id"], receive=True
        )
        if blocked_res["success"] and blocked_res["data"]:
            return ("You are blocked by Aikido Firewall.", 403)

    # Ratelimiting :
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
        message = "You are rate limited by Aikido firewall"
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
    if is_curr_route_useful:
        get_comms().send_data_to_bg_process("ROUTE", context)
