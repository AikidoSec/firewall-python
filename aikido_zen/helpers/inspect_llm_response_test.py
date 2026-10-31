from types import SimpleNamespace

import pytest

from aikido_zen.thread.thread_cache import get_cache
from .inspect_llm_response import (
    ANTHROPIC_MESSAGES,
    CHAT_COMPLETIONS,
    EMBEDDINGS,
    GEMINI,
    RESPONSES,
    inspect_llm_response,
    match_ai_request,
)


@pytest.fixture(autouse=True)
def setup():
    get_cache().reset()
    yield
    get_cache().reset()


def get_ai_stats():
    return get_cache().ai_stats.get_stats()


@pytest.mark.parametrize(
    "method, host, path, expected",
    [
        (
            "POST",
            "api.openai.com",
            "/v1/chat/completions",
            ("openai", CHAT_COMPLETIONS, None),
        ),
        (
            "POST",
            "my-resource.openai.azure.com",
            "/openai/deployments/gpt-5/chat/completions",
            ("azure", CHAT_COMPLETIONS, None),
        ),
        ("POST", "localhost", "/v1/responses", ("openai_compatible", RESPONSES, None)),
        (
            "POST",
            "litellm.internal",
            "/anthropic/v1/messages",
            ("anthropic_compatible", ANTHROPIC_MESSAGES, None),
        ),
        (
            "POST",
            "generativelanguage.googleapis.com",
            "/v1beta/models/gemini-2.5-flash:generateContent",
            ("gemini", GEMINI, "gemini-2.5-flash"),
        ),
        ("POST", "api.mistral.ai", "/v1/embeddings", ("mistral", EMBEDDINGS, None)),
        (
            "POST",
            "api.mistral.ai",
            "/v1/fim/completions",
            ("mistral", CHAT_COMPLETIONS, None),
        ),
        ("GET", "api.openai.com", "/v1/responses", None),
        ("POST", "api.anthropic.com", "/v1/messages/count_tokens", None),
        ("POST", "api.openai.com", "/v1/embeddings", None),
        (
            "POST",
            "api.eu.mistral.ai",
            "/v1/agents/completions",
            ("mistral", CHAT_COMPLETIONS, None),
        ),
        (
            "POST",
            "codestral.mistral.ai",
            "/v1/fim/completions",
            ("codestral", CHAT_COMPLETIONS, None),
        ),
        ("POST", "localhost", "/v1/fim/completions", None),
        (
            "POST",
            "generativelanguage.googleapis.com",
            "/v1beta/models/gemini-2.5-flash:streamGenerateContent",
            None,
        ),
        ("POST", None, "/v1/chat/completions", None),
    ],
)
def test_match_ai_request(method, host, path, expected):
    assert match_ai_request(method, host, path) == expected


def test_uncounted_response_does_not_match():
    inspect_llm_response(
        SimpleNamespace(),
        method="POST",
        host="gateway.example.com",
        path="/v1/chat/completions",
        status=200,
        body=b'{"id": "chatcmpl-c", "model": "m", "choices": []}',
        operation="httpx.Client.send",
    )
    assert get_ai_stats() == []


@pytest.mark.parametrize(
    "status, counted", [(199, 0), (200, 1), (201, 1), (299, 1), (300, 0), (500, 0)]
)
def test_only_2xx_responses_are_counted(status, counted):
    inspect_llm_response(
        SimpleNamespace(),
        method="POST",
        host="api.openai.com",
        path="/v1/chat/completions",
        status=status,
        body=b'{"model": "m", "choices": [], "usage": {"prompt_tokens": 1}}',
        operation="httpx.Client.send",
    )
    assert sum(s["calls"] for s in get_ai_stats()) == counted
