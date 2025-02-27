from aikido_zen import logger
from aikido_zen.context import Context
from aikido_zen.thread.thread_cache import get_cache


def on_init_request(context: Context):
    """
    This function gets the newly created context object and does the following :
    - Sets context object
    - Renews thread cache if necessary
    """
    if not context:
        return False  # Early return
    context.set_as_current_context()  # Store context object

    # Refresh thread cache
    thread_cache = get_cache()
    if thread_cache:
        thread_cache.renew_if_ttl_expired()  # Only check TTL at the start of a request.
        thread_cache.increment_stats()  # Increment request statistics if a context exists.
