"""
Counts LLM calls from the provider's response. The HTTP client sinks (httpx,
httpx2, requests, urllib3) count a POST whose path ends like an AI API, on any
host, as in firewall-node; the host only names the provider, and the body is
parsed only after the method and path match. The AI SDK sinks wrap their method
with `sdk_ai_call` and count only the calls no HTTP client sink counted.
"""

import contextvars
import json
import re
import threading
from collections import namedtuple

from aikido_zen.helpers.ai_provider_hosts import get_ai_provider
from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.on_ai_call import on_ai_call
from aikido_zen.helpers.register_call import register_call

# The fields of an API's response that hold the model, the answer and the usage.
AIFormat = namedtuple("AIFormat", "model answer usage input_tokens output_tokens")

CHAT_COMPLETIONS = AIFormat(
    "model", "choices", "usage", ("prompt_tokens",), ("completion_tokens",)
)
RESPONSES = AIFormat("model", "output", "usage", ("input_tokens",), ("output_tokens",))
ANTHROPIC_MESSAGES = AIFormat(
    "model", "content", "usage", ("input_tokens",), ("output_tokens",)
)
EMBEDDINGS = AIFormat(
    "model", "data", "usage", ("prompt_tokens",), ("completion_tokens",)
)
# promptTokenCount already includes the cached tokens.
GEMINI = AIFormat(
    "modelVersion",
    None,
    "usageMetadata",
    ("promptTokenCount", "toolUsePromptTokenCount"),
    ("candidatesTokenCount", "thoughtsTokenCount"),
)

GEMINI_PATH = re.compile(r"/models/([^/:]+):generateContent$")

# Mistral's other APIs that report usage. Their paths are generic, so they only
# match on Mistral's hosts.
MISTRAL_PATHS = {
    "/v1/agents/completions": CHAT_COMPLETIONS,
    "/v1/fim/completions": CHAT_COMPLETIONS,
    "/v1/embeddings": EMBEDDINGS,
}

# A redirect makes requests and urllib3 pass the final response through twice.
SEEN_ATTR = "_aikido_llm_seen"


class SdkCall:
    """One AI SDK method call. `counted_from_http` turns True when an HTTP client
    sink counts a response while it runs."""

    __slots__ = ("counted_from_http", "thread")

    def __init__(self):
        self.counted_from_http = False
        self.thread = threading.get_ident()


# The SDK call running in this context, or None. Copies of the context (a task, or
# `asyncio.to_thread`, started inside the call) share the object, so an HTTP request
# the SDK sends from there marks the same call. Each SDK call gets its own object.
_sdk_call = contextvars.ContextVar("aikido_llm_sdk_call", default=None)


def current_sdk_call():
    """
    The SDK call running in this thread, or None. A thread started during an SDK call
    can inherit its context (free-threaded 3.14 does), and must not treat its own
    later SDK calls as part of that one.
    """
    call = _sdk_call.get()
    if call is None or call.thread != threading.get_ident():
        return None
    return call


def match_ai_request(method, host, path):
    """
    Returns (provider, AIFormat, model from the path) for an AI API request, or
    None. `path` is the URL path without the query string.
    """
    if method != "POST" or not host:
        return None
    if path.endswith("/chat/completions"):
        return get_ai_provider(host, "openai_compatible"), CHAT_COMPLETIONS, None
    if path.endswith("/responses"):
        return get_ai_provider(host, "openai_compatible"), RESPONSES, None
    if path.endswith("/v1/messages"):
        return get_ai_provider(host, "anthropic_compatible"), ANTHROPIC_MESSAGES, None
    gemini = GEMINI_PATH.search(path) if path.endswith(":generateContent") else None
    if gemini:
        return get_ai_provider(host, "gemini_compatible"), GEMINI, gemini.group(1)
    if path in MISTRAL_PATHS:
        provider = get_ai_provider(host, None)
        if provider in ("mistral", "codestral"):
            return provider, MISTRAL_PATHS[path], None
    return None


def as_tokens(value):
    return value if isinstance(value, int) and value > 0 else 0


def get_tokens(body, ai_format):
    """(input, output) tokens, or None when the body is not that API's answer."""
    usage = body.get(ai_format.usage)
    if not isinstance(usage, dict):
        return None
    if ai_format.answer and not isinstance(body.get(ai_format.answer), list):
        return None
    return (
        sum(as_tokens(usage.get(field)) for field in ai_format.input_tokens),
        sum(as_tokens(usage.get(field)) for field in ai_format.output_tokens),
    )


def sdk_ai_call(on_response, is_async=False):
    """
    Wraps an AI SDK method. The HTTP client sinks see the provider's response during
    the method, so `on_response` (which counts it) runs only when none of them did.
    A wrapped SDK method that calls another wrapped one sees the same response, so
    only the outer one decides and the call is counted once.
    Errors in `on_response` are logged and never reach the app, as with `after`.
    """

    def inspect(func, instance, call, return_value):
        if call.counted_from_http:
            return
        try:
            on_response(instance, return_value)
        except Exception as e:
            logger.debug(
                "%s:%s ai sdk sink error: %s", func.__module__, func.__name__, e
            )

    def decorator(func, instance, args, kwargs):
        if current_sdk_call() is not None:
            return func(*args, **kwargs)
        call = SdkCall()
        token = _sdk_call.set(call)
        try:
            return_value = func(*args, **kwargs)
        finally:
            _sdk_call.reset(token)
        inspect(func, instance, call, return_value)
        return return_value

    async def decorator_async(func, instance, args, kwargs):
        if current_sdk_call() is not None:
            return await func(*args, **kwargs)
        call = SdkCall()
        token = _sdk_call.set(call)
        try:
            return_value = await func(*args, **kwargs)
        finally:
            _sdk_call.reset(token)
        inspect(func, instance, call, return_value)
        return return_value

    return decorator_async if is_async else decorator


def inspect_llm_response(response, *, method, host, path, status, body, operation):
    """
    Records usage for a finished AI API response. `body` must be the decoded
    bytes, or None when the client has not read the response (streaming): then
    nothing is inspected.
    """
    if body is None or getattr(response, SEEN_ATTR, False):
        return
    match = match_ai_request(method, host, path)
    # As in firewall-node: only a successful response is a finished call.
    if match is None or not 200 <= status < 300:
        return
    setattr(response, SEEN_ATTR, True)
    provider, ai_format, path_model = match

    parsed = json.loads(body)
    if not isinstance(parsed, dict):
        return
    tokens = get_tokens(parsed, ai_format)
    model = parsed.get(ai_format.model) or path_model
    # Error bodies have no model, and a response without usage has no tokens.
    if tokens is None or not isinstance(model, str):
        return

    register_call(operation, "ai_op")
    on_ai_call(
        provider=provider,
        model=model,
        input_tokens=tokens[0],
        output_tokens=tokens[1],
    )
    call = _sdk_call.get()
    if call is not None:
        call.counted_from_http = True
