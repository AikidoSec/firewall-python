from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import on_import, patch_function, after
from aikido_zen.storage.ai_statistics import on_ai_call


@after
def _create(func, instance, args, kwargs, return_value):
    op = "openai.resources.responses.responses.Responses.create"
    register_call(op, "ai_op")

    on_ai_call(
        provider="openai",
        model=return_value.get("model", ""),
        input_tokens=return_value.usage.input_tokens,
        output_tokens=return_value.usage.output_tokens,
    )


@on_import("openai.resources.responses.responses")
def patch(m):
    """
    patching module openai
    - patches function create(...) on Responses class, to inspect response
    """
    patch_function(m, "Responses.create", _create)
