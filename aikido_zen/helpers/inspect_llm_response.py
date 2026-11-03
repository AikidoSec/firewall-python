"""
Counts LLM calls from the provider's response. The HTTP client sinks (httpx,
httpx2, requests, urllib3) count a POST whose path ends like an AI API, on any
host, under the endpoint URL; the body is parsed only after the method and path
match. With AIKIDO_FEATURE_AI_SDK_FALLBACK, the AI SDK sinks wrap their method
with `sdk_ai_call` and also count the calls no HTTP client sink counted.
"""

import contextvars
import json
import re
import threading
from collections import namedtuple
from urllib.parse import unquote, urlsplit

from aikido_zen.helpers.env_vars.feature_flags import is_feature_enabled
from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.on_ai_call import on_ai_call
from aikido_zen.helpers.register_call import register_call

# The fields of an API's response that hold the model and the token counts. The
# input tokens include the cached ones, and cache_read and cache_write (key paths
# in the usage) are the cached part of them.
AIFormat = namedtuple(
    "AIFormat", "model usage input_tokens output_tokens cache_read cache_write"
)

CHAT_COMPLETIONS = AIFormat(
    "model",
    "usage",
    ("prompt_tokens",),
    ("completion_tokens",),
    ("prompt_tokens_details", "cached_tokens"),
    None,
)
RESPONSES = AIFormat(
    "model",
    "usage",
    ("input_tokens",),
    ("output_tokens",),
    ("input_tokens_details", "cached_tokens"),
    ("input_tokens_details", "cache_write_tokens"),
)
# Anthropic reports the cached tokens apart from input_tokens.
ANTHROPIC_MESSAGES = AIFormat(
    "model",
    "usage",
    ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"),
    ("output_tokens",),
    ("cache_read_input_tokens",),
    ("cache_creation_input_tokens",),
)
# Bedrock names the model in the path, as the botocore sink does.
BEDROCK_ANTHROPIC = ANTHROPIC_MESSAGES._replace(model=None)
EMBEDDINGS = AIFormat(
    "model", "usage", ("prompt_tokens",), ("completion_tokens",), None, None
)
# promptTokenCount already includes the cached tokens.
GEMINI = AIFormat(
    "modelVersion",
    "usageMetadata",
    ("promptTokenCount", "toolUsePromptTokenCount"),
    ("candidatesTokenCount", "thoughtsTokenCount"),
    ("cachedContentTokenCount",),
    None,
)

GEMINI_PATH = re.compile(r"/models/([^/:]+):generateContent$")
VERTEX_ANTHROPIC_PATH = re.compile(r"/publishers/anthropic/models/[^/:]+:rawPredict$")
# httpx decodes the path, so an inference profile ARN brings its "/" into it.
BEDROCK_INVOKE_PATH = re.compile(r"/model/(.+)/invoke$")

# Every path ending that match_ai_request accepts, so that most requests are
# turned down by one check.
AI_PATH_ENDINGS = (
    "/chat/completions",
    "/responses",
    "/v1/messages",
    ":generateContent",
    ":rawPredict",
    "/invoke",
    "/v1/agents/completions",
    "/v1/fim/completions",
    "/v1/embeddings",
)

DEFAULT_PORTS = {"http": 80, "https": 443}

# A redirect makes requests and urllib3 pass the final response through twice.
SEEN_ATTR = "_aikido_llm_seen"


class SdkCall:
    """One AI SDK method call. `counted_from_http` turns True when an HTTP client
    sink counts a response while it runs."""

    __slots__ = ("counted_from_http", "thread")

    def __init__(self):
        self.counted_from_http = False
        self.thread = threading.get_ident()


# The SDK call running in this context. A task or `asyncio.to_thread` started inside
# the call shares the object, so its HTTP request still marks the right call.
_sdk_call = contextvars.ContextVar("aikido_llm_sdk_call", default=None)


def current_sdk_call():
    """
    The SDK call running in this thread, or None. A new thread can inherit the
    context (free-threaded 3.14 does), but its later SDK calls are its own.
    """
    call = _sdk_call.get()
    if call is None or call.thread != threading.get_ident():
        return None
    return call


def match_ai_request(method, path):
    """
    Returns (AIFormat, model from the path) for an AI API request, or None.
    `path` is the URL path without the query string.
    """
    if method != "POST" or not path.endswith(AI_PATH_ENDINGS):
        return None
    if path.endswith("/chat/completions"):
        return CHAT_COMPLETIONS, None
    if path.endswith("/responses"):
        return RESPONSES, None
    if path.endswith("/v1/messages"):
        return ANTHROPIC_MESSAGES, None
    if path.endswith(":generateContent"):
        gemini = GEMINI_PATH.search(path)
        return (GEMINI, gemini.group(1)) if gemini else None
    if path.endswith(":rawPredict"):
        if VERTEX_ANTHROPIC_PATH.search(path):
            return ANTHROPIC_MESSAGES, None
        return None
    if path.endswith("/invoke"):
        return match_bedrock_invoke(path)
    if path.endswith(("/v1/agents/completions", "/v1/fim/completions")):
        return CHAT_COMPLETIONS, None
    if path.endswith("/v1/embeddings"):
        return EMBEDDINGS, None
    return None


def match_bedrock_invoke(path):
    bedrock = BEDROCK_INVOKE_PATH.search(path)
    if bedrock is None:
        return None
    model = unquote(bedrock.group(1))
    # An inference profile ARN does not name the model, so the body's is used.
    if model.startswith("arn:"):
        return ANTHROPIC_MESSAGES, None
    return BEDROCK_ANTHROPIC, model


def endpoint_url(scheme, host, port, path):
    """The URL a call is reported under: no user info, query or fragment."""
    if ":" in host:
        host = f"[{host}]"
    if port and port != DEFAULT_PORTS.get(scheme):
        host = f"{host}:{port}"
    return f"{scheme}://{host}{path}"


def sdk_endpoint_url(base_url, path):
    """The endpoint URL of an SDK call, from the client's base URL and the API path."""
    if base_url is None:
        return None
    url = urlsplit(str(base_url))
    if not url.hostname:
        return None
    return endpoint_url(url.scheme, url.hostname, url.port, url.path.rstrip("/") + path)


def as_tokens(value):
    return value if isinstance(value, int) and value > 0 else 0


def get_count(usage, key_path):
    if key_path is None:
        return 0
    for key in key_path:
        usage = usage.get(key) if isinstance(usage, dict) else None
    return as_tokens(usage)


def get_tokens(body, ai_format):
    """(input, output, cache read, cache write) tokens, all 0 without a usage."""
    usage = body.get(ai_format.usage)
    if not isinstance(usage, dict):
        return 0, 0, 0, 0
    return (
        sum(as_tokens(usage.get(field)) for field in ai_format.input_tokens),
        sum(as_tokens(usage.get(field)) for field in ai_format.output_tokens),
        get_count(usage, ai_format.cache_read),
        get_count(usage, ai_format.cache_write),
    )


def sdk_ai_call(on_response, is_async=False):
    """
    Wraps an AI SDK method. Only with AIKIDO_FEATURE_AI_SDK_FALLBACK, `on_response`
    counts the call when no HTTP client sink counted it during the method. Nested
    wrapped methods count once, in the outer one. Errors in `on_response` are
    logged, as with `after`.
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
        if not is_feature_enabled("ai_sdk_fallback") or current_sdk_call() is not None:
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
        if not is_feature_enabled("ai_sdk_fallback") or current_sdk_call() is not None:
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


def inspect_llm_response(
    response, *, method, scheme, host, port, path, status, body, operation
):
    """
    Records usage for a finished AI API response. `body` is the decoded bytes, or
    None for a streamed response, which is not inspected.
    """
    if body is None or not host or getattr(response, SEEN_ATTR, False):
        return
    match = match_ai_request(method, path)
    # Only a successful response is a finished call.
    if match is None or not 200 <= status < 300:
        return
    setattr(response, SEEN_ATTR, True)
    ai_format, path_model = match

    parsed = json.loads(body)
    if not isinstance(parsed, dict):
        return
    model = (parsed.get(ai_format.model) if ai_format.model else None) or path_model
    # Any matched response with a model counts, with 0 tokens when it has no usage.
    if not isinstance(model, str):
        return

    input_tokens, output_tokens, cache_read, cache_write = get_tokens(parsed, ai_format)
    register_call(operation, "ai_op")
    on_ai_call(
        provider=endpoint_url(scheme, host, port, path),
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read=cache_read,
        cache_write=cache_write,
    )
    call = _sdk_call.get()
    if call is not None:
        call.counted_from_http = True
