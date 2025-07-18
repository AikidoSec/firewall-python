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


@on_import("mistralai.agents", "mistralai", "1.0.0")
def patch_agents(m):
    patch_function(m, "Agents.complete", _chat_completions_response)


@on_import("mistralai.chat", "mistralai", "1.0.0")
def patch_chat(m):
    patch_function(m, "Chat.complete", _chat_completions_response)


@on_import("mistralai.embeddings", "mistralai", "1.0.0")
def patch_embeddings(m):
    patch_function(m, "Embeddings.create", _chat_completions_response)


@on_import("mistralai.fim", "mistralai", "1.0.0")
def patch_fim(m):
    patch_function(m, "Fim.complete", _chat_completions_response)
