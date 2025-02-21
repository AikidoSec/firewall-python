"""Exports request_handler function"""

import aikido_zen.background_process as communications
import aikido_zen.context as ctx
from aikido_zen.api_discovery.get_api_info import get_api_info
from aikido_zen.api_discovery.update_route_info import update_route_info
from aikido_zen.helpers.is_useful_route import is_useful_route
from aikido_zen.helpers.logging import logger
from aikido_zen.thread.thread_cache import get_cache
from .check_if_ip_blocked import check_if_ip_blocked


def request_handler(stage, status_code=0):
    """This will check for rate limiting, Allowed IP's, useful routes, etc."""
    try:
        if stage == "init":
            #  This gets executed the first time a request get's intercepted
            context = ctx.get_current_context()
            thread_cache = get_cache()
            if not context or not thread_cache:
                return

            thread_cache.increment_stats()  # Increment request statistics

            if thread_cache.is_bypassed_ip(context.remote_address):
                ctx.reset()  # Reset context object if it's a bypassed IP (no protection).
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
