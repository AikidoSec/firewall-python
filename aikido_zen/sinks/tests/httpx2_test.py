from urllib.parse import quote

import pytest

import aikido_zen.sinks.httpx2
from aikido_zen.test_utils.ai_network_capture import (
    INFERENCE_PROFILE_ARN,
    ORDER,
    assert_counted_once,
    break_reporting,
    enable_capture,
    get_ai_stats,
    run_in_protected_app,
    serve_provider,
    unreachable_url,
)
from aikido_zen.thread.thread_cache import get_cache

httpx2 = pytest.importorskip("httpx2")


@pytest.fixture(scope="module", autouse=True)
def enable_the_flag():
    enable_capture(aikido_zen.sinks.httpx2)


@pytest.fixture(scope="module")
def provider():
    with serve_provider() as url:
        yield url


@pytest.fixture(autouse=True)
def setup():
    get_cache().reset()
    yield
    get_cache().reset()


def test_httpx2_counts_once_and_body_stays_readable(provider):
    with httpx2.Client() as client:
        response = client.post(provider + "/v1/messages", json={})
    assert response.json()["model"] == "claude-sonnet-4-20250514"
    assert_counted_once(provider, "claude-sonnet-4-20250514", 21, 12)


@pytest.mark.asyncio
async def test_httpx2_async_counts_once(provider):
    async with httpx2.AsyncClient() as client:
        response = await client.post(provider + "/v1/chat/completions", json={})
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"
    assert_counted_once(provider, "gpt-4o-mini-2024-07-18", 11, 7)


def test_httpx2_gzip_body_is_parsed(provider):
    response = httpx2.post(provider + "/v1/chat/completions?gzip", json={})
    assert response.headers["Content-Encoding"] == "gzip"
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"
    assert_counted_once(provider, "gpt-4o-mini-2024-07-18", 11, 7)


@pytest.mark.asyncio
async def test_plain_httpx2_calls_are_unchanged(provider):
    url = provider + "/api/orders"
    with httpx2.Client() as client:
        assert client.get(url).json() == ORDER
        assert client.post(url, json={"order": 1}).json() == ORDER
    async with httpx2.AsyncClient() as client:
        assert (await client.get(url)).json() == ORDER
        assert (await client.post(url, json={"order": 1})).json() == ORDER
    assert get_ai_stats() == []


def test_httpx2_stream_is_not_read_and_not_counted(provider):
    with httpx2.Client() as client:
        with client.stream(
            "POST", provider + "/v1/chat/completions", json={"stream": True}
        ) as response:
            with pytest.raises(httpx2.ResponseNotRead):
                response.content
            assert b"[DONE]" in b"".join(response.iter_bytes())
    assert get_ai_stats() == []


@pytest.mark.asyncio
async def test_httpx2_async_stream_is_not_read_and_not_counted(provider):
    async with httpx2.AsyncClient() as client:
        async with client.stream(
            "POST", provider + "/v1/chat/completions", json={"stream": True}
        ) as response:
            with pytest.raises(httpx2.ResponseNotRead):
                response.content
            assert b"[DONE]" in b"".join([c async for c in response.aiter_bytes()])
    assert get_ai_stats() == []


def test_httpx2_reports_the_origin_without_user_info(provider):
    path = "/model/" + quote(INFERENCE_PROFILE_ARN, safe="") + "/invoke"
    url = provider.replace("http://", "http://user:secret@") + path + "?key=secret"
    httpx2.post(url, json={})
    assert [(s["provider"], s["calls"]) for s in get_ai_stats()] == [(provider, 1)]


def test_httpx2_redirect_counts_once(provider):
    with httpx2.Client(follow_redirects=True) as client:
        response = client.post(provider + "/redirect/v1/chat/completions", json={})
    assert response.history[0].status_code == 307
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"
    assert_counted_once(provider, "gpt-4o-mini-2024-07-18", 11, 7)


@pytest.mark.asyncio
async def test_httpx2_errors_still_reach_the_app():
    url = unreachable_url("/v1/chat/completions")
    with pytest.raises(httpx2.ConnectError):
        httpx2.post(url, json={})
    async with httpx2.AsyncClient() as client:
        with pytest.raises(httpx2.ConnectError):
            await client.post(url, json={})
    assert get_ai_stats() == []


@pytest.mark.asyncio
async def test_reporting_errors_do_not_break_httpx2_calls(provider, monkeypatch):
    break_reporting(monkeypatch)
    url = provider + "/v1/chat/completions"
    assert httpx2.post(url, json={}).json()["model"] == "gpt-4o-mini-2024-07-18"
    async with httpx2.AsyncClient() as client:
        response = await client.post(url, json={})
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"


@pytest.mark.parametrize("flag, patched", [(None, False), ("true", True)])
def test_httpx2_is_only_patched_and_counted_with_the_flag(provider, flag, patched):
    script = """
import json, sys
import httpx2
from aikido_zen.thread.thread_cache import get_cache

response = httpx2.post(sys.argv[1], json={})
print(json.dumps({
    "wrapped": [
        hasattr(httpx2.Client.send, "__wrapped__"),
        hasattr(httpx2.AsyncClient.send, "__wrapped__"),
    ],
    "model": response.json()["model"],
    "calls": [stats["calls"] for stats in get_cache().ai_stats.get_stats()],
}))
"""
    output = run_in_protected_app(script, flag, provider + "/v1/chat/completions")
    assert output == {
        "wrapped": [patched] * 2,
        "model": "gpt-4o-mini-2024-07-18",
        "calls": [1] if patched else [],
    }
