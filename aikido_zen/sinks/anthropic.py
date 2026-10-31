from aikido_zen.helpers.ai_provider_hosts import get_ai_provider
from aikido_zen.helpers.inspect_llm_response import sdk_ai_call
from aikido_zen.helpers.on_ai_call import on_ai_call
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import on_import, patch_function


def on_message(instance, message):
    # The SDK keeps its base URL only on the private client.
    base_url = getattr(getattr(instance, "_client", None), "base_url", None)
    host = getattr(base_url, "host", None)
    register_call("anthropic.resources.messages.messages.Messages.create", "ai_op")
    on_ai_call(
        provider=get_ai_provider(host, "anthropic_compatible") if host else "anthropic",
        model=message.model,
        input_tokens=message.usage.input_tokens,
        output_tokens=message.usage.output_tokens,
    )


@on_import("anthropic.resources.messages")
def patch(m):
    patch_function(m, "messages.Messages.create", sdk_ai_call(on_message))
    patch_function(
        m, "messages.AsyncMessages.create", sdk_ai_call(on_message, is_async=True)
    )
