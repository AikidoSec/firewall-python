"""
Counts AI API calls from the responses that the HTTP client sinks see, when
AIKIDO_FEATURE_AI_NETWORK_CAPTURE is on. Each call is reported under its endpoint URL.
"""

import json
import re
from collections import namedtuple
from urllib.parse import unquote

from aikido_zen.helpers.env_vars.feature_flags import is_feature_enabled
from aikido_zen.helpers.on_ai_call import on_ai_call

AICall = namedtuple("AICall", "model input_tokens output_tokens cache_read cache_write")

# Where an API's usage keeps each token count, as dotted key paths that are added up.
# The input is the provider's own count: OpenAI and Gemini include the cached tokens
# in it, Anthropic and Bedrock report them next to it.
TokenFields = namedtuple("TokenFields", "input output cache_read cache_write")
CHAT_COMPLETIONS = TokenFields(
    input=("prompt_tokens",),
    output=("completion_tokens",),
    cache_read=("prompt_tokens_details.cached_tokens",),
    cache_write=("prompt_tokens_details.cache_write_tokens",),
)
RESPONSES = TokenFields(
    input=("input_tokens",),
    output=("output_tokens",),
    cache_read=("input_tokens_details.cached_tokens",),
    cache_write=("input_tokens_details.cache_write_tokens",),
)
ANTHROPIC_MESSAGES = TokenFields(
    input=("input_tokens",),
    output=("output_tokens",),
    cache_read=("cache_read_input_tokens",),
    cache_write=("cache_creation_input_tokens",),
)
GEMINI = TokenFields(
    input=("promptTokenCount", "toolUsePromptTokenCount"),
    output=("candidatesTokenCount", "thoughtsTokenCount"),
    cache_read=("cachedContentTokenCount",),
    cache_write=(),
)
BEDROCK_CONVERSE = TokenFields(
    input=("inputTokens",),
    output=("outputTokens",),
    cache_read=("cacheReadInputTokens",),
    cache_write=("cacheWriteInputTokens",),
)

AI_PATH_ENDINGS = (
    "/chat/completions",
    "/responses",
    "/v1/messages",
    ":generateContent",
    ":rawPredict",
    "/converse",
    "/invoke",
)
GEMINI_PATH = re.compile(r"/models/([^/:]+):generateContent$")
VERTEX_ANTHROPIC_PATH = re.compile(r"/publishers/anthropic/models/[^/]+:rawPredict$")
BEDROCK_PATH = re.compile(r"/model/([^/]+)/(converse|invoke)$")

DEFAULT_PORTS = {"http": 80, "https": 443}

# A redirect makes requests and urllib3 pass the final response through twice.
SEEN_ATTR = "_aikido_ai_seen"


def is_ai_network_capture_enabled():
    return is_feature_enabled("ai_network_capture")


def is_ai_request_path(path):
    return path.endswith(AI_PATH_ENDINGS)


def parse_ai_response(path, body):
    """The AICall of an AI API response, or None."""
    found = find_api(path, body) if isinstance(body, dict) else None
    if found is None:
        return None
    model, usage, fields = found
    if not isinstance(model, str) or not model:
        return None
    if not isinstance(usage, dict):
        usage = {}
    return AICall(
        model,
        count_tokens(usage, fields.input),
        count_tokens(usage, fields.output),
        count_tokens(usage, fields.cache_read),
        count_tokens(usage, fields.cache_write),
    )


def find_api(path, body):
    """(model, usage, TokenFields) of the API that the path belongs to, or None."""
    if path.endswith("/chat/completions"):
        return body.get("model"), body.get("usage"), CHAT_COMPLETIONS
    if path.endswith("/responses"):
        return body.get("model"), body.get("usage"), RESPONSES
    if path.endswith("/v1/messages") or VERTEX_ANTHROPIC_PATH.search(path):
        return body.get("model"), body.get("usage"), ANTHROPIC_MESSAGES
    gemini = GEMINI_PATH.search(path)
    if gemini:
        version = body.get("modelVersion")
        model = version if isinstance(version, str) and version else gemini.group(1)
        return model, body.get("usageMetadata"), GEMINI
    bedrock = BEDROCK_PATH.search(path)
    if bedrock:
        model = unquote(bedrock.group(1))
        # An inference profile ARN does not name the model, so the body's is used.
        if model.startswith("arn:"):
            model = body.get("model")
        if bedrock.group(2) == "converse":
            return model, body.get("usage"), BEDROCK_CONVERSE
        return model, body.get("usage"), ANTHROPIC_MESSAGES
    return None


def count_tokens(usage, fields):
    total = 0
    for field in fields:
        value = usage
        for key in field.split("."):
            value = value.get(key) if isinstance(value, dict) else None
        if isinstance(value, int) and value > 0:
            total += value
    return total


def endpoint_url(scheme, host, port, path):
    """The URL a call is reported under: no user info, query or fragment."""
    if ":" in host:
        host = f"[{host}]"
    if port and port != DEFAULT_PORTS.get(scheme):
        host = f"{host}:{port}"
    return f"{scheme}://{host}{path}"


def inspect_ai_response(response, *, method, scheme, host, port, path, status, body):
    """`path` is the encoded URL path without the query string, `body` is None for a
    streamed response."""
    if body is None or not host or getattr(response, SEEN_ATTR, False):
        return
    # Only a successful response is a finished call.
    if method != "POST" or not is_ai_request_path(path) or not 200 <= status < 300:
        return
    setattr(response, SEEN_ATTR, True)
    call = parse_ai_response(path, json.loads(body))
    if call is None:
        return
    on_ai_call(
        provider=endpoint_url(scheme, host, port, path),
        model=call.model,
        input_tokens=call.input_tokens,
        output_tokens=call.output_tokens,
        cache_read=call.cache_read,
        cache_write=call.cache_write,
    )
