"""
patching module openai
- patches create(...) and parse(...) on Responses, to inspect response
- patches create(...), update(...) and parse(...) on chat Completions, to inspect response
- each also on its async class; counts only what no HTTP client sink counted
"""

from aikido_zen.helpers.ai_provider_hosts import get_ai_provider
from aikido_zen.helpers.inspect_llm_response import sdk_ai_call
from aikido_zen.helpers.on_ai_call import on_ai_call
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import on_import, patch_function


def ensure_parsed_response(return_value):
    rv_class = getattr(getattr(return_value, "__class__", None), "__name__", None)
    if rv_class == "LegacyAPIResponse":
        # The functions we wrap can give back a legacy api response if asked for by the user, we parse this.
        return return_value.parse()

    return return_value


def get_provider(instance):
    # The SDK keeps its base URL only on the private client.
    base_url = getattr(getattr(instance, "_client", None), "base_url", None)
    host = getattr(base_url, "host", None)
    return get_ai_provider(host, "openai_compatible") if host else "openai"


def on_response(func_name):
    def inspect(instance, return_value):
        res = ensure_parsed_response(return_value)
        register_call(
            f"openai.resources.responses.responses.Responses.{func_name}", "ai_op"
        )
        on_ai_call(
            provider=get_provider(instance),
            model=res.model,
            input_tokens=res.usage.input_tokens,
            output_tokens=res.usage.output_tokens,
        )

    return inspect


def on_completion(func_name):
    def inspect(instance, return_value):
        res = ensure_parsed_response(return_value)
        register_call(
            f"openai.resources.chat.completions.completions.Completions.{func_name}",
            "ai_op",
        )
        on_ai_call(
            provider=get_provider(instance),
            model=res.model,
            input_tokens=res.usage.prompt_tokens,
            output_tokens=res.usage.completion_tokens,
        )

    return inspect


@on_import("openai.resources.responses.responses", "openai", "1.0")
def patch_responses(m):
    patch_function(m, "Responses.create", sdk_ai_call(on_response("create")))
    patch_function(m, "Responses.parse", sdk_ai_call(on_response("parse")))
    patch_function(
        m, "AsyncResponses.create", sdk_ai_call(on_response("create"), is_async=True)
    )
    patch_function(
        m, "AsyncResponses.parse", sdk_ai_call(on_response("parse"), is_async=True)
    )


@on_import("openai.resources.chat.completions.completions", "openai", "1.0")
def patch_chat_completions(m):
    patch_function(m, "Completions.create", sdk_ai_call(on_completion("create")))
    patch_function(m, "Completions.update", sdk_ai_call(on_completion("update")))
    patch_function(m, "Completions.parse", sdk_ai_call(on_completion("parse")))
    patch_function(
        m,
        "AsyncCompletions.create",
        sdk_ai_call(on_completion("create"), is_async=True),
    )
    patch_function(
        m,
        "AsyncCompletions.update",
        sdk_ai_call(on_completion("update"), is_async=True),
    )
    patch_function(
        m,
        "AsyncCompletions.parse",
        sdk_ai_call(on_completion("parse"), is_async=True),
    )


# Before openai 1.92, structured outputs lived in beta.chat.completions.parse.
@on_import("openai.resources.beta.chat.completions", "openai", "1.0")
def patch_beta_chat_completions(m):
    patch_function(m, "Completions.parse", sdk_ai_call(on_completion("parse")))
    patch_function(
        m,
        "AsyncCompletions.parse",
        sdk_ai_call(on_completion("parse"), is_async=True),
    )
