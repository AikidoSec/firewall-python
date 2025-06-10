from aikido_zen.helpers.on_ai_call import on_ai_call
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import on_import, patch_function, after


@after
def _create(func, instance, args, kwargs, return_value):
    op = "openai.resources.responses.responses.Responses.create"
    register_call(op, "ai_op")

    on_ai_call(
        provider="openai",
        model=return_value.model,
        input_tokens=return_value.usage.input_tokens,
        output_tokens=return_value.usage.output_tokens,
    )


@on_import("openai.resources.responses.responses", "openai", version_requirement="1.0")
def patch(m):
    """
    patching module openai
    - patches function create(...) on Responses class, to inspect response
    """
    patch_function(m, "Responses.create", _create)
