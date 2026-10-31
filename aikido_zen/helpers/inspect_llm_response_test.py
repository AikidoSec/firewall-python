import asyncio
import contextvars
import json
import threading
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
    sdk_ai_call,
)


@pytest.fixture(autouse=True)
def setup():
    get_cache().reset()
    yield
    get_cache().reset()


def count_response(response_id, host="api.openai.com", model="gpt-4o-mini"):
    body = {
        "model": model,
        "choices": [],
        "usage": {"prompt_tokens": 1, "completion_tokens": 2},
    }
    if response_id is not None:
        body["id"] = response_id
    inspect_llm_response(
        SimpleNamespace(),
        method="POST",
        host=host,
        path="/v1/chat/completions",
        status=200,
        body=json.dumps(body).encode(),
        operation="httpx.Client.send",
    )


def sdk_response(response_id, model="gpt-4o-mini"):
    return SimpleNamespace(id=response_id, model=model)


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


def sdk_method(host_counts):
    def method():
        if host_counts:
            count_response("chatcmpl-a")
        return sdk_response("chatcmpl-a")

    return method


def on_sdk_response(instance, response):
    get_cache().ai_stats.on_ai_call("sdk", response.model, 1, 2)


@pytest.mark.parametrize(
    "http_counts, expected", [(True, ["openai"]), (False, ["sdk"])]
)
def test_sdk_sink_counts_only_what_the_http_sinks_did_not(http_counts, expected):
    wrapped = sdk_ai_call(on_sdk_response)
    wrapped(sdk_method(http_counts), None, (), {})
    assert [s["provider"] for s in get_ai_stats()] == expected


def test_http_count_outside_an_sdk_call_does_not_hide_the_next_one():
    count_response("chatcmpl-a")
    sdk_ai_call(on_sdk_response)(sdk_method(False), None, (), {})
    assert [s["provider"] for s in get_ai_stats()] == ["openai", "sdk"]


def test_http_count_in_a_task_started_by_the_sdk_call_counts_once():
    async def send():
        count_response("chatcmpl-a")

    async def method():
        await asyncio.ensure_future(send())
        return sdk_response("chatcmpl-a")

    asyncio.run(sdk_ai_call(on_sdk_response, is_async=True)(method, None, (), {}))
    assert [s["provider"] for s in get_ai_stats()] == ["openai"]


def test_http_count_in_a_worker_thread_that_has_the_call_context_counts_once():
    async def method():
        context = contextvars.copy_context()
        await asyncio.get_running_loop().run_in_executor(
            None, context.run, count_response, "chatcmpl-a"
        )
        return sdk_response("chatcmpl-a")

    asyncio.run(sdk_ai_call(on_sdk_response, is_async=True)(method, None, (), {}))
    assert [s["provider"] for s in get_ai_stats()] == ["openai"]


def test_http_count_in_another_sdk_call_does_not_hide_this_one():
    def other_call():
        sdk_ai_call(on_sdk_response)(sdk_method(True), None, (), {})

    def method():
        thread = threading.Thread(target=other_call)
        thread.start()
        thread.join()
        return sdk_response("chatcmpl-b")

    sdk_ai_call(on_sdk_response)(method, None, (), {})
    assert sorted(s["provider"] for s in get_ai_stats()) == ["openai", "sdk"]


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


def test_sdk_sink_error_does_not_reach_the_app():
    def broken(instance, response):
        raise ValueError("boom")

    assert sdk_ai_call(broken)(sdk_method(False), None, (), {}).id == "chatcmpl-a"
