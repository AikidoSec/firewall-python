"""Exports function should_block_request"""

from aikido_zen.helpers.logging import logger
from aikido_zen.context import get_current_context
from aikido_zen.thread.thread_cache import get_cache
import aikido_zen.background_process.comms as c
from aikido_zen.ratelimiting.get_ratelimited_endpoint import get_ratelimited_endpoint
from aikido_zen.helpers.match_endpoints import match_endpoints


def should_block_request():
    """
    Checks for rate-limiting and checks if the current user is blocked.
    """
    try:
        context = get_current_context()
        cache = get_cache()
        if not context or not cache:
            return {"block": False}

        context.executed_middleware = (
            True  # Update context with middleware execution set to true
        )
        context.set_as_current_context()

        # Make sure we set middleware installed to true (reports back to core) :
        cache.middleware_installed = True

        # Blocked users:
        if context.user and cache.is_user_blocked(context.user["id"]):
            return {"block": True, "type": "blocked", "trigger": "user"}

        route_metadata = context.get_route_metadata()
        endpoints = cache.get_endpoints()
        comms = c.get_comms()
        if not comms or not endpoints:
            return {"block": False}
        matched_endpoints = match_endpoints(route_metadata, endpoints)
        # Ratelimiting :
        if matched_endpoints and get_ratelimited_endpoint(
            matched_endpoints, context.route
        ):
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
                return {
                    "block": True,
                    "type": "ratelimited",
                    "trigger": ratelimit_res["data"]["trigger"],
                    "ip": context.remote_address,
                }
    except Exception as e:
        logger.debug("Exception occurred in should_block_request: %s", e)
    return {"block": False}
