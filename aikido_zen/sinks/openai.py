"""
patching module openai
- patches function create(...) on Responses class, to inspect response
- patches function create(...) on Completions class, to inspect response
"""

from aikido_zen.helpers.on_ai_call import on_ai_call
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import on_import, patch_function, after


@after
def _create_responses(func, instance, args, kwargs, return_value):
    op = f"openai.resources.responses.responses.Responses.{func.__name__}"
    register_call(op, "ai_op")

    on_ai_call(
        provider="openai",
        model=return_value.model,
        input_tokens=return_value.usage.input_tokens,
        output_tokens=return_value.usage.output_tokens,
    )


@after
def _create_completions(func, instance, args, kwargs, return_value):
    op = f"openai.resources.chat.completions.completions.Completions.{func.__name__}"
    register_call(op, "ai_op")

    on_ai_call(
        provider="openai",
        model=return_value.model,
        input_tokens=return_value.usage.prompt_tokens,
        output_tokens=return_value.usage.completion_tokens,
    )


@on_import("openai.resources.responses.responses", "openai", "1.0")
def patch_responses(m):
    patch_function(m, "Responses.create", _create_responses)
    patch_function(m, "Responses.parse", _create_responses)


@on_import("openai.resources.chat.completions.completions", "openai", "1.0")
def patch_chat_completions(m):
    patch_function(m, "Completions.create", _create_completions)
    patch_function(m, "Completions.update", _create_completions)
