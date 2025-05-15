"""Helper function file, see function docstring"""

from aikido_zen.helpers.check_env_for_blocking import check_env_for_blocking
from aikido_zen.thread.thread_cache import get_cache


def is_blocking_enabled():
    """Checks with the process cache for blocking, and if that is not defined, checks env"""
    if get_cache() and get_cache().config and get_cache().config.blocking is not None:
        return get_cache().config.blocking
    return check_env_for_blocking()
