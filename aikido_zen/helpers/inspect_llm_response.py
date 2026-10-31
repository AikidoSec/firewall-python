"""
Shared by the HTTP client sinks (httpx, httpx2, requests, urllib3) that see
finished responses. As in firewall-node, a POST whose path ends like an AI API
is an AI call on any host, and the host only names the provider. The body is
parsed only after the method and path match.
"""

import json
import re
from collections import namedtuple

from aikido_zen.helpers.ai_provider_hosts import get_ai_provider
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
