from urllib.parse import urlsplit

from aikido_zen.helpers.ai_provider_hosts import get_ai_provider
from aikido_zen.helpers.inspect_llm_response import sdk_ai_call
from aikido_zen.helpers.on_ai_call import on_ai_call
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import on_import, patch_function


def get_provider(instance):
    try:
        server_url, _ = instance.sdk_configuration.get_server_details()
        host = urlsplit(server_url).hostname
    except Exception:
        host = None
    return get_ai_provider(host, "openai_compatible") if host else "mistral"


def on_completion(name):
    def inspect(instance, return_value):
        register_call(
            f"{instance.__module__}.{instance.__class__.__name__}.{name}", "ai_op"
        )
        on_ai_call(
            provider=get_provider(instance),
            model=return_value.model,
            input_tokens=return_value.usage.prompt_tokens,
            output_tokens=return_value.usage.completion_tokens,
        )

    return inspect


@on_import("mistralai.agents", "mistralai", "1.0.0")
def patch_agents(m):
    patch_function(m, "Agents.complete", sdk_ai_call(on_completion("complete")))


@on_import("mistralai.chat", "mistralai", "1.0.0")
def patch_chat(m):
    patch_function(m, "Chat.complete", sdk_ai_call(on_completion("complete")))


@on_import("mistralai.embeddings", "mistralai", "1.0.0")
def patch_embeddings(m):
    patch_function(m, "Embeddings.create", sdk_ai_call(on_completion("create")))


@on_import("mistralai.fim", "mistralai", "1.0.0")
def patch_fim(m):
    patch_function(m, "Fim.complete", sdk_ai_call(on_completion("complete")))
