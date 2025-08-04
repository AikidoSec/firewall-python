from aikido_zen.helpers.on_ai_call import on_ai_call
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import on_import, patch_function, after, after_async


@after
def _messages_create(func, instance, args, kwargs, return_value):
    op = f"anthropic.resources.messages.messages.Messages.create"
    register_call(op, "ai_op")

    on_ai_call(
        provider="anthropic",
        model=return_value.model,
        input_tokens=return_value.usage.input_tokens,
        output_tokens=return_value.usage.output_tokens,
    )


@after_async
async def _messages_create_async(func, instance, args, kwargs, return_value):
    op = f"anthropic.resources.messages.messages.Messages.create"
    register_call(op, "ai_op")

    on_ai_call(
        provider="anthropic",
        model=return_value.model,
        input_tokens=return_value.usage.input_tokens,
        output_tokens=return_value.usage.output_tokens,
    )


@on_import("anthropic.resources.messages")
def patch(m):
    patch_function(m, "messages.Messages.create", _messages_create)
    patch_function(m, "messages.AsyncMessages.create", _messages_create_async)
