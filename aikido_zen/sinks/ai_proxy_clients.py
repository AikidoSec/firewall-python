"""
Pins the Anthropic and OpenAI SDK clients to the local AI proxy, so its L7
engine can see tool definitions/schemas and tool calls, and enforce blocking.

Patches the SDK client constructors rather than `Messages.create`/
`Responses.create` (see sinks/anthropic.py, sinks/openai.py) because the proxy
needs to sit on the transport, not observe the finished response.

Only touches clients constructed with no `http_client` of their own. A caller
that supplies its own `http_client` (e.g. `langchain_anthropic`,
`langchain_openai`) is left untouched for now rather than risk breaking their
transport configuration.
"""

from aikido_zen.ai_proxy.transport import LazyZenAsyncTransport, LazyZenTransport
from aikido_zen.sinks import before, on_import, patch_function


@before
def _inject_anthropic_sync(func, instance, args, kwargs):
    if kwargs.get("http_client") is not None:
        return
    import anthropic

    kwargs["http_client"] = anthropic.DefaultHttpxClient(
        mounts={"all://": LazyZenTransport()}
    )


@before
def _inject_anthropic_async(func, instance, args, kwargs):
    if kwargs.get("http_client") is not None:
        return
    import anthropic

    kwargs["http_client"] = anthropic.DefaultAsyncHttpxClient(
        mounts={"all://": LazyZenAsyncTransport()}
    )


@before
def _inject_openai_sync(func, instance, args, kwargs):
    if kwargs.get("http_client") is not None:
        return
    import openai

    kwargs["http_client"] = openai.DefaultHttpxClient(
        mounts={"all://": LazyZenTransport()}
    )


@before
def _inject_openai_async(func, instance, args, kwargs):
    if kwargs.get("http_client") is not None:
        return
    import openai

    kwargs["http_client"] = openai.DefaultAsyncHttpxClient(
        mounts={"all://": LazyZenAsyncTransport()}
    )


@on_import("anthropic")
def patch_anthropic(m):
    patch_function(m, "Anthropic.__init__", _inject_anthropic_sync)
    patch_function(m, "AsyncAnthropic.__init__", _inject_anthropic_async)


@on_import("openai")
def patch_openai(m):
    patch_function(m, "OpenAI.__init__", _inject_openai_sync)
    patch_function(m, "AsyncOpenAI.__init__", _inject_openai_async)
