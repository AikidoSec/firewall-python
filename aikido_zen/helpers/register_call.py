from aikido_zen.thread.thread_cache import get_cache

PERF_SKIP_REGISTER_CALL = True


def register_call(operation, kind):
    if PERF_SKIP_REGISTER_CALL:
        return  # Do not register call
    cache = get_cache()
    if cache:
        cache.stats.operations.register_call(operation, kind)
