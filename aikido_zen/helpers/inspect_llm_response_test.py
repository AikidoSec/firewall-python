import asyncio
import contextvars
import json
import threading
from types import SimpleNamespace

import pytest

from aikido_zen.thread.thread_cache import get_cache
from .inspect_llm_response import (
    ANTHROPIC_MESSAGES,
    BEDROCK_ANTHROPIC,
    CHAT_COMPLETIONS,
    EMBEDDINGS,
    GEMINI,
    RESPONSES,
    _sdk_call,
    endpoint_url,
    get_tokens,
    inspect_llm_response,
    match_ai_request,
    sdk_ai_call,
    sdk_endpoint_url,
)

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
VERTEX_PATH = "/v1/projects/p/locations/us-east5/publishers/anthropic/models/"
BEDROCK_MODEL = "anthropic.claude-haiku-4-5-20251001-v1:0"
INFERENCE_PROFILE_ARN = (
    "arn:aws:bedrock:us-east-1:123456789012:inference-profile/us.anthropic.claude"
)


@pytest.fixture(autouse=True)
def setup():
    get_cache().reset()
    yield
    get_cache().reset()


@pytest.fixture
def sdk_fallback(monkeypatch):
    monkeypatch.setenv("AIKIDO_FEATURE_AI_SDK_FALLBACK", "true")


def inspect(body, path="/v1/chat/completions", status=200, host="api.openai.com"):
    inspect_llm_response(
        SimpleNamespace(),
        method="POST",
        scheme="https",
        host=host,
        port=None,
        path=path,
        status=status,
        body=json.dumps(body).encode(),
        operation="httpx.Client.send",
    )


def count_response(response_id):
    inspect(
        {
            "id": response_id,
            "model": "gpt-4o-mini",
            "choices": [],
            "usage": {"prompt_tokens": 1, "completion_tokens": 2},
        }
    )


def sdk_response(response_id, model="gpt-4o-mini"):
    return SimpleNamespace(id=response_id, model=model)


def get_ai_stats():
    return get_cache().ai_stats.get_stats()


@pytest.mark.parametrize(
    "method, path, expected",
    [
        ("POST", "/v1/chat/completions", (CHAT_COMPLETIONS, None)),
        (
            "POST",
            "/openai/deployments/gpt-5/chat/completions",
            (CHAT_COMPLETIONS, None),
        ),
        ("POST", "/v1/responses", (RESPONSES, None)),
        ("POST", "/anthropic/v1/messages", (ANTHROPIC_MESSAGES, None)),
        (
            "POST",
            "/v1beta/models/gemini-2.5-flash:generateContent",
            (GEMINI, "gemini-2.5-flash"),
        ),
        (
            "POST",
            VERTEX_PATH + "claude-haiku-4-5@20251001:rawPredict",
            (ANTHROPIC_MESSAGES, None),
        ),
        (
            "POST",
            "/model/" + BEDROCK_MODEL + "/invoke",
            (BEDROCK_ANTHROPIC, BEDROCK_MODEL),
        ),
        (
            "POST",
            "/model/us.anthropic.claude-haiku-4-5-20251001-v1%3A0/invoke",
            (BEDROCK_ANTHROPIC, "us.anthropic.claude-haiku-4-5-20251001-v1:0"),
        ),
        (
            "POST",
            "/model/" + INFERENCE_PROFILE_ARN + "/invoke",
            (ANTHROPIC_MESSAGES, None),
        ),
        (
            "POST",
            "/model/arn%3Aaws%3Abedrock%3Aus-east-1%3A1%3Ainference-profile%2Fx/invoke",
            (ANTHROPIC_MESSAGES, None),
        ),
        ("POST", "/v1/embeddings", (EMBEDDINGS, None)),
        ("POST", "/v1/fim/completions", (CHAT_COMPLETIONS, None)),
        ("POST", "/proxy/v1/agents/completions", (CHAT_COMPLETIONS, None)),
        ("GET", "/v1/responses", None),
        ("POST", "/v1/messages/count_tokens", None),
        ("POST", "/v1/completions", None),
        ("POST", "/v1beta/models/gemini-2.5-flash:streamGenerateContent", None),
        (
            "POST",
            "/v1/projects/p/locations/l/publishers/google/models/gemini:rawPredict",
            None,
        ),
        ("POST", "/model/" + BEDROCK_MODEL + "/invoke-with-response-stream", None),
        ("POST", "/2015-03-31/functions/f/invoke", None),
    ],
)
def test_match_ai_request(method, path, expected):
    assert match_ai_request(method, path) == expected


@pytest.mark.parametrize(
    "scheme, host, port, path, expected",
    [
        (
            "https",
            "api.openai.com",
            None,
            "/v1/responses",
            "https://api.openai.com/v1/responses",
        ),
        (
            "https",
            "api.openai.com",
            443,
            "/v1/responses",
            "https://api.openai.com/v1/responses",
        ),
        ("http", "127.0.0.1", 80, "/v1/messages", "http://127.0.0.1/v1/messages"),
        (
            "http",
            "localhost",
            11434,
            "/v1/chat/completions",
            "http://localhost:11434/v1/chat/completions",
        ),
        (
            "https",
            "gw.example.com",
            80,
            "/v1/responses",
            "https://gw.example.com:80/v1/responses",
        ),
        ("http", "::1", 8080, "/v1/responses", "http://[::1]:8080/v1/responses"),
    ],
)
def test_endpoint_url(scheme, host, port, path, expected):
    assert endpoint_url(scheme, host, port, path) == expected


@pytest.mark.parametrize(
    "base_url, path, expected",
    [
        ("https://api.openai.com/v1/", "/chat/completions", OPENAI_URL),
        (
            "https://api.anthropic.com",
            "/v1/messages",
            "https://api.anthropic.com/v1/messages",
        ),
        (
            "https://user:secret@gw.example.com:8443/openai/v1?key=secret#top",
            "/responses",
            "https://gw.example.com:8443/openai/v1/responses",
        ),
        (None, "/v1/messages", None),
        ("not a url", "/v1/messages", None),
    ],
)
def test_sdk_endpoint_url(base_url, path, expected):
    assert sdk_endpoint_url(base_url, path) == expected


@pytest.mark.parametrize(
    "ai_format, body, expected",
    [
        (
            CHAT_COMPLETIONS,
            {
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 20,
                    "prompt_tokens_details": {"cached_tokens": 40},
                }
            },
            (100, 20, 40, 0),
        ),
        (
            RESPONSES,
            {
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 20,
                    "input_tokens_details": {
                        "cached_tokens": 40,
                        "cache_write_tokens": 5,
                    },
                }
            },
            (100, 20, 40, 5),
        ),
        (
            ANTHROPIC_MESSAGES,
            {
                "usage": {
                    "input_tokens": 60,
                    "cache_read_input_tokens": 40,
                    "cache_creation_input_tokens": 5,
                    "output_tokens": 20,
                }
            },
            (105, 20, 40, 5),
        ),
        (
            GEMINI,
            {
                "usageMetadata": {
                    "promptTokenCount": 100,
                    "toolUsePromptTokenCount": 10,
                    "cachedContentTokenCount": 40,
                    "candidatesTokenCount": 20,
                    "thoughtsTokenCount": 5,
                }
            },
            (110, 25, 40, 0),
        ),
        (
            EMBEDDINGS,
            {"usage": {"prompt_tokens": 15, "total_tokens": 15}},
            (15, 0, 0, 0),
        ),
        (CHAT_COMPLETIONS, {}, (0, 0, 0, 0)),
        (
            CHAT_COMPLETIONS,
            {
                "usage": {
                    "prompt_tokens": -1,
                    "completion_tokens": "7",
                    "prompt_tokens_details": None,
                }
            },
            (0, 0, 0, 0),
        ),
    ],
)
def test_tokens_per_format(ai_format, body, expected):
    assert get_tokens(body, ai_format) == expected


def test_response_is_reported_under_its_endpoint_url():
    count_response("chatcmpl-a")
    assert get_ai_stats() == [
        {
            "provider": OPENAI_URL,
            "model": "gpt-4o-mini",
            "calls": 1,
            "tokens": {"input": 1, "output": 2, "total": 3},
        }
    ]


def test_cache_tokens_are_reported_when_the_provider_has_them():
    inspect(
        {
            "model": "claude-haiku-4-5-20251001",
            "content": [],
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
        "input": 50020,
        "output": 300,
        "total": 50320,
        "cacheRead": 50000,
    }


def test_response_without_a_host_is_not_counted():
    inspect({"model": "m"}, host=None)
    assert get_ai_stats() == []


def test_body_with_a_model_but_without_usage_counts_with_zero_tokens():
    inspect({"id": "chatcmpl-c", "model": "m"})
    assert get_ai_stats() == [
        {
            "provider": OPENAI_URL,
            "model": "m",
            "calls": 1,
            "tokens": {"input": 0, "output": 0, "total": 0},
        }
    ]


@pytest.mark.parametrize(
    "body",
    [
        {"usage": {"prompt_tokens": 1}},
        {"model": "", "usage": {"prompt_tokens": 1}},
        {"model": 5, "usage": {"prompt_tokens": 1}},
        [{"model": "m"}],
    ],
)
def test_body_without_a_model_is_not_counted(body):
    inspect(body)
    assert get_ai_stats() == []


def test_vertex_count_tokens_is_not_counted():
    inspect(
        {"input_tokens": 12},
        path=VERTEX_PATH + "count-tokens:rawPredict",
        host="aiplatform.googleapis.com",
    )
    assert get_ai_stats() == []


def test_bedrock_reports_the_model_of_the_path():
    message = {
        "type": "message",
        "model": "claude-haiku-4-5-20251001",
        "content": [],
        "usage": {"input_tokens": 3, "output_tokens": 4},
    }
    host = "bedrock-runtime.us-east-1.amazonaws.com"
    inspect(message, path="/model/" + BEDROCK_MODEL + "/invoke", host=host)
    inspect(message, path="/model/" + INFERENCE_PROFILE_ARN + "/invoke", host=host)
    assert [(s["provider"], s["model"]) for s in get_ai_stats()] == [
        ("https://" + host + "/model/" + BEDROCK_MODEL + "/invoke", BEDROCK_MODEL),
        (
            "https://" + host + "/model/" + INFERENCE_PROFILE_ARN + "/invoke",
            "claude-haiku-4-5-20251001",
        ),
    ]


def sdk_method(host_counts):
    def method():
        if host_counts:
            count_response("chatcmpl-a")
        return sdk_response("chatcmpl-a")

    return method


def on_sdk_response(instance, response):
    get_cache().ai_stats.on_ai_call("sdk", response.model, 1, 2)


def test_sdk_sink_counts_nothing_without_the_fallback_flag(monkeypatch):
    monkeypatch.delenv("AIKIDO_FEATURE_AI_SDK_FALLBACK", raising=False)

    def method():
        assert _sdk_call.get() is None
        return sdk_response("chatcmpl-a")

    assert sdk_ai_call(on_sdk_response)(method, None, (), {}).id == "chatcmpl-a"
    assert get_ai_stats() == []


@pytest.mark.parametrize(
    "http_counts, expected", [(True, [OPENAI_URL]), (False, ["sdk"])]
)
def test_sdk_sink_counts_only_what_the_http_sinks_did_not(
    sdk_fallback, http_counts, expected
):
    wrapped = sdk_ai_call(on_sdk_response)
    wrapped(sdk_method(http_counts), None, (), {})
    assert [s["provider"] for s in get_ai_stats()] == expected


def test_http_count_outside_an_sdk_call_does_not_hide_the_next_one(sdk_fallback):
    count_response("chatcmpl-a")
    sdk_ai_call(on_sdk_response)(sdk_method(False), None, (), {})
    assert [s["provider"] for s in get_ai_stats()] == [OPENAI_URL, "sdk"]


def test_http_count_in_a_task_started_by_the_sdk_call_counts_once(sdk_fallback):
    async def send():
        count_response("chatcmpl-a")

    async def method():
        await asyncio.ensure_future(send())
        return sdk_response("chatcmpl-a")

    asyncio.run(sdk_ai_call(on_sdk_response, is_async=True)(method, None, (), {}))
    assert [s["provider"] for s in get_ai_stats()] == [OPENAI_URL]


def test_http_count_in_a_worker_thread_that_has_the_call_context_counts_once(
    sdk_fallback,
):
    async def method():
        context = contextvars.copy_context()
        await asyncio.get_running_loop().run_in_executor(
            None, context.run, count_response, "chatcmpl-a"
        )
        return sdk_response("chatcmpl-a")

    asyncio.run(sdk_ai_call(on_sdk_response, is_async=True)(method, None, (), {}))
    assert [s["provider"] for s in get_ai_stats()] == [OPENAI_URL]


def test_http_count_in_another_sdk_call_does_not_hide_this_one(sdk_fallback):
    def other_call():
        sdk_ai_call(on_sdk_response)(sdk_method(True), None, (), {})

    def method():
        thread = threading.Thread(target=other_call)
        thread.start()
        thread.join()
        return sdk_response("chatcmpl-b")

    sdk_ai_call(on_sdk_response)(method, None, (), {})
    assert sorted(s["provider"] for s in get_ai_stats()) == [OPENAI_URL, "sdk"]


@pytest.mark.parametrize(
    "status, counted", [(199, 0), (200, 1), (201, 1), (299, 1), (300, 0), (500, 0)]
)
def test_only_2xx_responses_are_counted(status, counted):
    inspect({"model": "m", "usage": {"prompt_tokens": 1}}, status=status)
    assert sum(s["calls"] for s in get_ai_stats()) == counted


def test_sdk_sink_error_does_not_reach_the_app(sdk_fallback):
    def broken(instance, response):
        raise ValueError("boom")

    assert sdk_ai_call(broken)(sdk_method(False), None, (), {}).id == "chatcmpl-a"
