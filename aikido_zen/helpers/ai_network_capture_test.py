import json
from types import SimpleNamespace
from urllib.parse import quote

import pytest

from aikido_zen.thread.thread_cache import get_cache
from .ai_network_capture import (
    endpoint_url,
    inspect_ai_response,
    is_ai_request_path,
    parse_ai_response,
)

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
VERTEX_PATH = "/v1/projects/p/locations/us-east5/publishers/anthropic/models/"
BEDROCK_MODEL = "anthropic.claude-haiku-4-5-20251001-v1:0"
INFERENCE_PROFILE_ARN = (
    "arn:aws:bedrock:us-east-1:123456789012:inference-profile/us.anthropic.claude"
)
RECORDED_OPENAI_CACHE_HIT = {
    "completion_tokens": 5,
    "completion_tokens_details": {
        "accepted_prediction_tokens": 0,
        "audio_tokens": 0,
        "reasoning_tokens": 0,
        "rejected_prediction_tokens": 0,
    },
    "prompt_tokens": 8413,
    "prompt_tokens_details": {"audio_tokens": 0, "cached_tokens": 8320},
    "total_tokens": 8418,
}
RECORDED_ANTHROPIC_CACHE_WRITE = {
    "cache_creation": {
        "ephemeral_1h_input_tokens": 0,
        "ephemeral_5m_input_tokens": 9601,
    },
    "cache_creation_input_tokens": 9601,
    "cache_read_input_tokens": 0,
    "inference_geo": "not_available",
    "input_tokens": 8,
    "output_tokens": 5,
    "service_tier": "standard",
    "speed": "standard",
}
RECORDED_ANTHROPIC_CACHE_READ = {
    **RECORDED_ANTHROPIC_CACHE_WRITE,
    "cache_creation": {"ephemeral_1h_input_tokens": 0, "ephemeral_5m_input_tokens": 0},
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 9601,
}
MESSAGE = {
    "type": "message",
    "model": "claude-haiku-4-5-20251001",
    "content": [],
    "usage": {"input_tokens": 3, "output_tokens": 4},
}


@pytest.fixture(autouse=True)
def setup():
    get_cache().reset()
    yield
    get_cache().reset()


def get_ai_stats():
    return get_cache().ai_stats.get_stats()


def inspect(body, path="/v1/chat/completions", method="POST", status=200, **kwargs):
    inspect_ai_response(
        kwargs.get("response", SimpleNamespace()),
        method=method,
        scheme="https",
        host=kwargs.get("host", "api.openai.com"),
        port=None,
        path=path,
        status=status,
        body=json.dumps(body).encode() if body is not None else None,
    )


@pytest.mark.parametrize(
    "path, expected",
    [
        ("/v1/chat/completions", True),
        ("/proxy/v1/chat/completions", True),
        ("/v1/responses", True),
        ("/v1/messages", True),
        ("/v1beta/models/gemini-2.5-flash:generateContent", True),
        (VERTEX_PATH + "claude-haiku-4-5@20251001:rawPredict", True),
        ("/model/" + BEDROCK_MODEL + "/converse", True),
        ("/model/" + BEDROCK_MODEL + "/invoke", True),
        ("/v1/messages/count_tokens", False),
        ("/v1/embeddings", False),
        ("/v1/completions", False),
        ("/v1beta/models/gemini-2.5-flash:streamGenerateContent", False),
        ("/model/" + BEDROCK_MODEL + "/invoke-with-response-stream", False),
        ("/api/orders", False),
    ],
)
def test_is_ai_request_path(path, expected):
    assert is_ai_request_path(path) is expected


@pytest.mark.parametrize(
    "path, body, expected",
    [
        (
            "/v1/chat/completions",
            {
                "model": "gpt-4o-mini",
                "usage": {"prompt_tokens": 11, "completion_tokens": 7},
            },
            ("gpt-4o-mini", 11, 7, 0, 0),
        ),
        (
            "/v1/responses",
            {"model": "gpt-4o", "usage": {"input_tokens": 20, "output_tokens": 9}},
            ("gpt-4o", 20, 9, 0, 0),
        ),
        ("/v1/messages", MESSAGE, ("claude-haiku-4-5-20251001", 3, 4, 0, 0)),
        (
            VERTEX_PATH + "claude-haiku-4-5@20251001:rawPredict",
            MESSAGE,
            ("claude-haiku-4-5-20251001", 3, 4, 0, 0),
        ),
        (VERTEX_PATH + "count-tokens:rawPredict", {"input_tokens": 12}, None),
        (
            "/v1/projects/p/locations/l/publishers/google/models/gemini:rawPredict",
            MESSAGE,
            None,
        ),
        (
            "/v1beta/models/gemini-2.5-flash:generateContent",
            {
                "modelVersion": "gemini-2.5-flash-001",
                "usageMetadata": {
                    "promptTokenCount": 70,
                    "toolUsePromptTokenCount": 30,
                    "candidatesTokenCount": 8,
                    "thoughtsTokenCount": 500,
                },
            },
            ("gemini-2.5-flash-001", 100, 508, 0, 0),
        ),
        (
            "/v1beta/models/gemini-2.5-flash:generateContent",
            {"candidates": []},
            ("gemini-2.5-flash", 0, 0, 0, 0),
        ),
        (
            "/model/" + BEDROCK_MODEL + "/converse",
            {"output": {}, "usage": {"inputTokens": 10, "outputTokens": 5}},
            (BEDROCK_MODEL, 10, 5, 0, 0),
        ),
        ("/model/" + BEDROCK_MODEL + "/invoke", MESSAGE, (BEDROCK_MODEL, 3, 4, 0, 0)),
        (
            "/model/us.anthropic.claude-haiku-4-5-20251001-v1%3A0/invoke",
            MESSAGE,
            ("us.anthropic.claude-haiku-4-5-20251001-v1:0", 3, 4, 0, 0),
        ),
        (
            "/model/" + quote(INFERENCE_PROFILE_ARN, safe="") + "/invoke",
            MESSAGE,
            ("claude-haiku-4-5-20251001", 3, 4, 0, 0),
        ),
        (
            "/model/" + quote(INFERENCE_PROFILE_ARN, safe="") + "/converse",
            {"output": {}, "usage": {"inputTokens": 10, "outputTokens": 5}},
            None,
        ),
        ("/model/" + INFERENCE_PROFILE_ARN + "/invoke", MESSAGE, None),
        ("/v1/chat/completions", {"id": "chatcmpl-1", "model": "m"}, ("m", 0, 0, 0, 0)),
        (
            "/v1/chat/completions",
            {"model": "m", "usage": {"prompt_tokens": -1, "completion_tokens": "7"}},
            ("m", 0, 0, 0, 0),
        ),
        ("/v1/chat/completions", {"usage": {"prompt_tokens": 1}}, None),
        ("/v1/chat/completions", {"model": ""}, None),
        ("/v1/chat/completions", {"model": 5}, None),
        ("/v1/chat/completions", [{"model": "m"}], None),
    ],
)
def test_parse_ai_response(path, body, expected):
    assert parse_ai_response(path, body) == expected


@pytest.mark.parametrize(
    "path, usage, expected",
    [
        ("/v1/chat/completions", RECORDED_OPENAI_CACHE_HIT, (8413, 5, 8320, 0)),
        ("/v1/messages", RECORDED_ANTHROPIC_CACHE_WRITE, (8, 5, 0, 9601)),
        ("/v1/messages", RECORDED_ANTHROPIC_CACHE_READ, (8, 5, 9601, 0)),
        (
            "/v1/chat/completions",
            {
                "prompt_tokens": 100,
                "completion_tokens": 20,
                "prompt_tokens_details": {"cached_tokens": 40, "cache_write_tokens": 5},
            },
            (100, 20, 40, 5),
        ),
        (
            "/v1/responses",
            {
                "input_tokens": 100,
                "output_tokens": 20,
                "input_tokens_details": {"cached_tokens": 40, "cache_write_tokens": 5},
            },
            (100, 20, 40, 5),
        ),
        (
            "/v1/messages",
            {
                "input_tokens": 60,
                "output_tokens": 20,
                "cache_read_input_tokens": 40,
                "cache_creation_input_tokens": 5,
            },
            (60, 20, 40, 5),
        ),
        (
            "/model/" + BEDROCK_MODEL + "/invoke",
            {
                "input_tokens": 60,
                "output_tokens": 20,
                "cache_read_input_tokens": 40,
                "cache_creation_input_tokens": 5,
            },
            (60, 20, 40, 5),
        ),
        (
            "/model/" + BEDROCK_MODEL + "/converse",
            {
                "inputTokens": 60,
                "outputTokens": 20,
                "cacheReadInputTokens": 40,
                "cacheWriteInputTokens": 5,
            },
            (60, 20, 40, 5),
        ),
        (
            "/v1/chat/completions",
            {"prompt_tokens": 100, "prompt_tokens_details": None},
            (100, 0, 0, 0),
        ),
    ],
)
def test_cache_tokens_per_format(path, usage, expected):
    assert parse_ai_response(path, {"model": "m", "usage": usage})[1:] == expected


def test_gemini_cached_tokens():
    body = {
        "usageMetadata": {
            "promptTokenCount": 100,
            "cachedContentTokenCount": 40,
            "candidatesTokenCount": 20,
        }
    }
    path = "/v1beta/models/gemini-2.5-flash:generateContent"
    assert parse_ai_response(path, body) == ("gemini-2.5-flash", 100, 20, 40, 0)


def test_cache_tokens_are_reported_when_the_provider_has_them():
    inspect(
        {
            "model": "claude-haiku-4-5-20251001",
            "usage": {
                "input_tokens": 20,
                "cache_read_input_tokens": 50000,
                "output_tokens": 300,
            },
        },
        path="/v1/messages",
        host="api.anthropic.com",
    )
    assert get_ai_stats()[0]["tokens"] == {
        "input": 20,
        "output": 300,
        "total": 320,
        "cacheRead": 50000,
    }


@pytest.mark.parametrize(
    "scheme, host, port, expected",
    [
        ("https", "api.openai.com", None, "https://api.openai.com/v1/responses"),
        ("https", "api.openai.com", 443, "https://api.openai.com/v1/responses"),
        ("http", "127.0.0.1", 80, "http://127.0.0.1/v1/responses"),
        ("http", "localhost", 11434, "http://localhost:11434/v1/responses"),
        ("https", "gw.example.com", 80, "https://gw.example.com:80/v1/responses"),
        ("http", "::1", 8080, "http://[::1]:8080/v1/responses"),
    ],
)
def test_endpoint_url(scheme, host, port, expected):
    assert endpoint_url(scheme, host, port, "/v1/responses") == expected


def test_response_is_reported_under_its_endpoint_url():
    inspect(
        {
            "model": "gpt-4o-mini",
            "usage": {"prompt_tokens": 1, "completion_tokens": 2},
        }
    )
    assert get_ai_stats() == [
        {
            "provider": OPENAI_URL,
            "model": "gpt-4o-mini",
            "calls": 1,
            "tokens": {"input": 1, "output": 2, "total": 3},
        }
    ]


@pytest.mark.parametrize(
    "status, counted", [(199, 0), (200, 1), (201, 1), (299, 1), (300, 0), (500, 0)]
)
def test_only_2xx_responses_are_counted(status, counted):
    inspect({"model": "m"}, status=status)
    assert sum(s["calls"] for s in get_ai_stats()) == counted


@pytest.mark.parametrize(
    "kwargs",
    [
        {"method": "GET"},
        {"path": "/v1/embeddings"},
        {"host": None},
        {"host": ""},
    ],
)
def test_other_requests_are_not_counted(kwargs):
    inspect({"model": "m"}, **kwargs)
    assert get_ai_stats() == []


def test_streamed_response_is_not_counted():
    inspect(None)
    assert get_ai_stats() == []


def test_same_response_is_counted_once():
    response = SimpleNamespace()
    inspect({"model": "m"}, response=response)
    inspect({"model": "m"}, response=response)
    assert get_ai_stats()[0]["calls"] == 1
