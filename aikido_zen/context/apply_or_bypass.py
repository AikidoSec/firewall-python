"""
Helper that either sets the request context as current OR marks the request
as bypassed (when the remote IP is in the bypass list).
"""

from aikido_zen.helpers.logging import logger
from aikido_zen.storage import bypassed_context_store
from aikido_zen.thread.thread_cache import get_cache
from . import current_context


def apply_context_or_bypass(context):
    """
    For bypassed IPs: clears the current context and sets the bypassed flag.
    For other IPs:    sets the context as current and clears the bypassed flag.

    Mirrors the firewall-java BypassedContextStore approach so almost every
    blocking site short-circuits naturally on `if not context: return`.
    """
    try:
        cache = get_cache()
        if (
            cache
            and context
            and context.remote_address
            and cache.is_bypassed_ip(context.remote_address)
        ):
            current_context.set(None)
            bypassed_context_store.set_bypassed(True)
            return

        bypassed_context_store.set_bypassed(False)
        if context:
            context.set_as_current_context()
    except Exception as e:
        logger.debug("Exception in apply_context_or_bypass: %s", e)
        # On error, fall back to the previous behaviour (set context).
        bypassed_context_store.set_bypassed(False)
        if context:
            context.set_as_current_context()
