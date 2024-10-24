"""
Exports should_block_request function
"""

from aikido_zen.context import get_current_context
from aikido_zen.thread.thread_cache import get_cache
from aikido_zen.background_process.comms import get_comms


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

        # agent.onMiddlewareExecuted

        # Blocked users:
        if context.user and cache.is_user_blocked(context.user["id"]):
            return {"block": True, "type": "blocked", "trigger": "user"}

        route_metadata = context.get_route_metadata()
        comms = get_comms()
        if not comms:
            return {"block": False}
        # Rate-limit :
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
    except Exception:
        pass
    return {"block": False}