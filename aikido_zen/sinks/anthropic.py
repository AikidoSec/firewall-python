from aikido_zen.helpers.inspect_llm_response import sdk_ai_call, sdk_endpoint_url
from aikido_zen.helpers.on_ai_call import on_ai_call
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import on_import, patch_function


def on_message(instance, message):
    # The SDK keeps its base URL only on the private client.
    base_url = getattr(getattr(instance, "_client", None), "base_url", None)
    usage = message.usage
    # The input tokens include the cached ones, which Anthropic reports apart.
    cache_read = getattr(usage, "cache_read_input_tokens", None) or 0
    cache_write = getattr(usage, "cache_creation_input_tokens", None) or 0
    register_call("anthropic.resources.messages.messages.Messages.create", "ai_op")
    on_ai_call(
        provider=sdk_endpoint_url(base_url, "/v1/messages"),
        model=message.model,
        input_tokens=usage.input_tokens + cache_read + cache_write,
        output_tokens=usage.output_tokens,
        cache_read=cache_read,
        cache_write=cache_write,
    )


@on_import("anthropic.resources.messages")
def patch(m):
    patch_function(m, "messages.Messages.create", sdk_ai_call(on_message))
    patch_function(
        m, "messages.AsyncMessages.create", sdk_ai_call(on_message, is_async=True)
    )
