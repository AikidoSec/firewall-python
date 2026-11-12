from aikido_zen.thread.thread_cache import get_cache


def on_ai_call(
    provider, model, input_tokens, output_tokens, cache_read=0, cache_write=0
):
    thread_cache = get_cache()
    if thread_cache:
        thread_cache.ai_stats.on_ai_call(
            provider, model, input_tokens, output_tokens, cache_read, cache_write
        )


def on_ai_tool_calls(provider, model, tool_names):
    thread_cache = get_cache()
    if thread_cache:
        for name in tool_names:
            thread_cache.ai_stats.on_ai_tool_call(provider, model, name)
