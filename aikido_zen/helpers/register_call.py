from aikido_zen.thread.thread_cache import get_cache


def register_call(operation, kind):
    cache = get_cache()
    if cache:
        cache.stats.operations.register_call(operation, kind)
