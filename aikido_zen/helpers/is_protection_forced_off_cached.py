from aikido_zen.thread.thread_cache import get_cache
from aikido_zen.helpers.protection_forced_off import protection_forced_off
from aikido_zen.context import Context


def is_protection_forced_off_cached(context: Context) -> bool:
    """
    Check if protection is forced off using cached endpoints.
    This function assumes that the thread cache has already been retrieved
    and uses it to determine if protection is forced off for the given context.
    """
    if not context:
        return False

    if context.protection_forced_off is not None:
        # Retrieving from cache, we don't want to constantly go through
        # all the endpoints for every single vulnerability check.
        return context.protection_forced_off

    thread_cache = get_cache()
    if not thread_cache:
        return False

    is_forced_off = protection_forced_off(
        context.get_route_metadata(), thread_cache.get_endpoints()
    )
    context.set_force_protection_off(is_forced_off)
    context.set_as_current_context()

    return is_forced_off
