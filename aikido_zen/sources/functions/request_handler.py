"""Exports request_handler function"""

import aikido_zen.context as ctx
from aikido_zen.api_discovery.update_route_info import update_route_info_from_context
from aikido_zen.helpers.is_useful_route import is_useful_route
from aikido_zen.helpers.logging import logger
from aikido_zen.thread.thread_cache import get_cache
from .ip_allowed_to_access_route import ip_allowed_to_access_route
import aikido_zen.background_process.comms as c


def request_handler(stage, status_code=0):
    """This will check for rate limiting, Allowed IP's, useful routes, etc."""
    try:
        if stage == "init":
            cache = get_cache()
            if ctx.get_current_context() and cache:
                cache.stats.increment_total_hits()
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

    # Do a check on firewall lists, this happens in background because of the heavy data.
    # For the timeout we notice the request during heavy loads usually takes 2ms - 2.5ms, we set timeout at 10ms.
    # That way we have a very small timeout with very little risk of not blocking ips.
    comms = c.get_comms()
    check_fw_lists_res = comms.send_data_to_bg_process(
        action="CHECK_FIREWALL_LISTS",
        obj={
            "ip": context.remote_address,
            "user-agent": context.get_user_agent(),
        },
        receive=True,
        timeout_in_sec=(10 / 1000),
    )
    if not check_fw_lists_res["success"] or not check_fw_lists_res["data"]["blocked"]:
        return

    block_type = check_fw_lists_res["data"]["type"]

    if block_type == "allowlist":
        message = "Your IP address is not allowed."
        message += " (Your IP: " + context.remote_address + ")"
        return message, 403
    if block_type == "blocklist":
        message = "Your IP address is blocked due to "
        message += check_fw_lists_res["data"]["reason"]
        message += " (Your IP: " + context.remote_address + ")"
        return message, 403
    if block_type == "bot-blocking":
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

        # api spec generation
        route = cache.routes.get(route_metadata)
        update_route_info_from_context(context, route)
