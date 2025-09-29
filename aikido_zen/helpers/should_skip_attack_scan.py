from aikido_zen.thread.thread_cache import get_cache
from aikido_zen.helpers.protection_forced_off import protection_forced_off
from aikido_zen.helpers.logging import logger
from aikido_zen.context import Context


def should_skip_attack_scan(context: Context) -> bool:
    """
    Check if protection is forced off or IP bypassed using cache stored in the context.
    This function assumes that the thread cache has already been retrieved
    and uses it to determine if protection is forced off for the given context.
    """
    if not context:
        return False

    if context.should_skip_attack_scan is not None:
        # Retrieving from cache, we don't want to constantly go through
        # all the endpoints for every single vulnerability check.
        return context.should_skip_attack_scan

    thread_cache = get_cache()
    if not thread_cache:
        return False

    is_forced_off = False
    # We check for a boolean protectionForcedOff on the matching endpoints, allows users to disable scans on certain routes.
    if protection_forced_off(
        context.get_route_metadata(), thread_cache.get_endpoints()
    ):
        is_forced_off = True
    # We check for Bypassed IPs : Allows users to let their DAST not be blocked by Zen
    if thread_cache.is_bypassed_ip(context.remote_address):
        is_forced_off = True

    context.set_force_protection_off(is_forced_off)
    context.set_as_current_context()

    return is_forced_off
