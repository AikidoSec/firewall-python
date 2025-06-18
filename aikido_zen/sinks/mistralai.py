from aikido_zen.helpers.on_ai_call import on_ai_call
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import on_import, patch_function, after


@after
def _chat_completions_response(func, instance, args, kwargs, return_value):
    op = f"{instance.__module__}.{instance.__class__.__name__}.{func.__name__}"
    register_call(op, "ai_op")

    on_ai_call(
        provider="mistralai",
        model=return_value.model,
        input_tokens=return_value.usage.prompt_tokens,
        output_tokens=return_value.usage.completion_tokens,
    )



@on_import("mistralai", "mistralai", "1.0.0")
def patch(m):
    """
    patching module mistralai
    - patches function agents.Agents.complete, returns ChatCompletionResponse
    - patches function chat.Chat.complete, returns ChatCompletionResponse
    """
    patch_function(m, "agents.Agents.complete", _chat_completions_response)
    # patch_function(m, "chat.Chat.parse", _chat_completions_response)
    patch_function(m, "chat.Chat.complete", _chat_completions_response)
    patch_function(m, "embeddings.Embeddings.create", _chat_completions_response)
    patch_function(m, "fim.Fim.complete", _chat_completions_response)
