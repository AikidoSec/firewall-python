from aikido_zen.helpers.on_ai_call import on_ai_call
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import on_import, patch_function, after, after_async


def get_provider_and_model_from_groq_model(groq_model: str):
    # e.g. return_value.model = 'openai/gpt-oss-20b'
    provider = groq_model.split("/")[0]
    model = "/".join(groq_model.split("/")[1:])
    return provider, model


@after
def _completions_create(func, instance, args, kwargs, return_value):
    op = "groq.resources.chat.completions.Completions.create"
    register_call(op, "ai_op")

    provider, model = get_provider_and_model_from_groq_model(return_value.model)
    on_ai_call(
        provider=provider,
        model=model,
        input_tokens=return_value.usage.prompt_tokens,
        output_tokens=return_value.usage.completion_tokens,
    )


@after_async
async def _completions_create_async(func, instance, args, kwargs, return_value):
    op = "groq.resources.chat.completions.AsyncCompletions.create"
    register_call(op, "ai_op")

    provider, model = get_provider_and_model_from_groq_model(return_value.model)
    on_ai_call(
        provider=provider,
        model=model,
        input_tokens=return_value.usage.prompt_tokens,
        output_tokens=return_value.usage.completion_tokens,
    )


@on_import("groq.resources.chat.completions")
def patch(m):
    patch_function(m, "Completions.create", _completions_create)
    patch_function(m, "AsyncCompletions.create", _completions_create_async)
