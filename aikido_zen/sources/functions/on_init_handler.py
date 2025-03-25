from aikido_zen.context import Context
from aikido_zen.thread.thread_cache import get_cache


def on_init_handler(context: Context):
    """
    On-Init Handler should be called after a context has been created, the function will :
    - Store context
    - Renew thread cache if necessary and store the hits
    - Check if IP is bypassed
    """
    if context is None:
        return

    cache = get_cache()
    if cache is not None and cache.is_bypassed_ip(context.remote_address):
        return  # Do not store the context of bypassed IPs, skip request processing.
    context.set_as_current_context()

    if cache is not None:
        # Only check the TTL at the start of a request.
        cache.renew_if_ttl_expired()
        cache.increment_stats()
