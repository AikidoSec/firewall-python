from aikido_zen.thread.thread_cache import get_cache


def on_ai_call(
    provider, model, input_tokens, output_tokens, cache_read=0, cache_write=0
):
    cache = get_cache()
    if cache:
        cache.ai_stats.on_ai_call(
            provider, model, input_tokens, output_tokens, cache_read, cache_write
        )
