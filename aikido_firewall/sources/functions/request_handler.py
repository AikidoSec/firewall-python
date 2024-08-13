"""Exports request_handler function"""

from aikido_firewall.background_process import get_comms
from aikido_firewall.context import get_current_context
from aikido_firewall.helpers.is_useful_route import is_useful_route


def request_handler(stage, status_code=0):
    """This will check for rate limiting, Allowed IP's, useful routes, etc."""
    if stage == "init":
        #  This gets executed the first time a request get's intercepted
        get_comms().send_data_to_bg_process("STATISTICS", {"action": "request"})
    elif stage == "pre_response":
        return pre_response()
    elif stage == "post_response":
        return post_response(status_code)


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
        return
    compressed_context = context.compress()

    # IP Allowlist:
    res = comms.send_data_to_bg_process(
        action="IS_IP_ALLOWED", obj=(compressed_context,), receive=True
    )
    if res["success"] and not res["data"]:
        message = "Your IP address is not allowed to access this resource."
        if context.remote_address:
            message += f" (Your IP: {compressed_context.remote_address})"
        return (message, 403)

    # Blocked users:
    if context.user:
        blocked_res = comms.send_data_to_bg_process(
            action="SHOULD_BLOCK_USER", obj=compressed_context.user["id"], receive=True
        )
        if blocked_res["success"] and blocked_res["data"]:
            return ("You are blocked by Aikido Firewall.", 403)

    # Ratelimiting :
    ratelimit_res = comms.send_data_to_bg_process(
        action="SHOULD_RATELIMIT", obj=compressed_context, receive=True
    )
    if ratelimit_res["success"] and ratelimit_res["data"]["block"]:

        message = "You are rate limited by Aikido firewall"
        if ratelimit_res["data"]["trigger"] is "ip":
            message += f" (Your IP: {compressed_context.remote_address})"
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
        get_comms().send_data_to_bg_process("ROUTE", (context.method, context.route))
