from aikido_zen.helpers.inspect_llm_response import sdk_ai_call, sdk_endpoint_url
from aikido_zen.helpers.on_ai_call import on_ai_call
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import on_import, patch_function


def get_provider(instance, path):
    server_url, _ = instance.sdk_configuration.get_server_details()
    return sdk_endpoint_url(server_url, path)


def on_completion(name, path):
    def inspect(instance, return_value):
        register_call(
            f"{instance.__module__}.{instance.__class__.__name__}.{name}", "ai_op"
        )
        on_ai_call(
            provider=get_provider(instance, path),
            model=return_value.model,
            input_tokens=return_value.usage.prompt_tokens,
            output_tokens=return_value.usage.completion_tokens,
        )

    return inspect


@on_import("mistralai.agents", "mistralai", "1.0.0")
def patch_agents(m):
    patch_function(
        m,
        "Agents.complete",
        sdk_ai_call(on_completion("complete", "/v1/agents/completions")),
    )


@on_import("mistralai.chat", "mistralai", "1.0.0")
def patch_chat(m):
    patch_function(
        m,
        "Chat.complete",
        sdk_ai_call(on_completion("complete", "/v1/chat/completions")),
    )


@on_import("mistralai.embeddings", "mistralai", "1.0.0")
def patch_embeddings(m):
    patch_function(
        m, "Embeddings.create", sdk_ai_call(on_completion("create", "/v1/embeddings"))
    )


@on_import("mistralai.fim", "mistralai", "1.0.0")
def patch_fim(m):
    patch_function(
        m, "Fim.complete", sdk_ai_call(on_completion("complete", "/v1/fim/completions"))
    )
