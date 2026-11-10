import httpx
import pytest

import aikido_zen.sinks.httpx
from aikido_zen.test_utils.ai_network_capture import (
    ORDER,
    assert_counted_once,
    break_reporting,
    enable_capture,
    get_ai_stats,
    serve_provider,
    unreachable_url,
)
from aikido_zen.thread.thread_cache import get_cache


@pytest.fixture(scope="module", autouse=True)
def enable_the_flag():
    enable_capture(aikido_zen.sinks.httpx)


@pytest.fixture(scope="module")
def provider():
    with serve_provider() as url:
        yield url


@pytest.fixture(autouse=True)
def setup():
    get_cache().reset()
    yield
    get_cache().reset()


def test_httpx_counts_once_and_body_stays_readable(provider):
    with httpx.Client() as client:
        response = client.post(provider + "/v1/responses", json={})
    assert response.json()["model"] == "gpt-4o-2024-08-06"
    assert_counted_once(provider, "gpt-4o-2024-08-06", 20, 9)


@pytest.mark.asyncio
async def test_httpx_async_counts_once(provider):
    async with httpx.AsyncClient() as client:
        response = await client.post(provider + "/v1/chat/completions", json={})
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"
    assert_counted_once(provider, "gpt-4o-mini-2024-07-18", 11, 7)


def test_httpx_gzip_body_is_parsed(provider):
    response = httpx.post(provider + "/v1/chat/completions?gzip", json={})
    assert response.headers["Content-Encoding"] == "gzip"
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"
    assert_counted_once(provider, "gpt-4o-mini-2024-07-18", 11, 7)


@pytest.mark.asyncio
async def test_plain_httpx_calls_are_unchanged(provider):
    url = provider + "/api/orders"
    with httpx.Client() as client:
        assert client.get(url).json() == ORDER
        assert client.post(url, json={"order": 1}).json() == ORDER
    async with httpx.AsyncClient() as client:
        assert (await client.get(url)).json() == ORDER
        assert (await client.post(url, json={"order": 1})).json() == ORDER
    assert get_ai_stats() == []


def test_httpx_stream_is_not_read_and_not_counted(provider):
    with httpx.Client() as client:
        with client.stream(
            "POST", provider + "/v1/chat/completions", json={"stream": True}
        ) as response:
            with pytest.raises(httpx.ResponseNotRead):
                response.content
            assert b"[DONE]" in b"".join(response.iter_bytes())
    assert get_ai_stats() == []


@pytest.mark.asyncio
async def test_httpx_async_stream_is_not_read_and_not_counted(provider):
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST", provider + "/v1/chat/completions", json={"stream": True}
        ) as response:
            with pytest.raises(httpx.ResponseNotRead):
                response.content
            assert b"[DONE]" in b"".join([c async for c in response.aiter_bytes()])
    assert get_ai_stats() == []


def test_httpx_redirect_counts_once(provider):
    with httpx.Client(follow_redirects=True) as client:
        response = client.post(provider + "/redirect/v1/chat/completions", json={})
    assert response.history[0].status_code == 307
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"
    assert_counted_once(provider, "gpt-4o-mini-2024-07-18", 11, 7)


@pytest.mark.asyncio
async def test_httpx_errors_still_reach_the_app():
    url = unreachable_url("/v1/chat/completions")
    with pytest.raises(httpx.ConnectError):
        httpx.post(url, json={})
    async with httpx.AsyncClient() as client:
        with pytest.raises(httpx.ConnectError):
            await client.post(url, json={})
    assert get_ai_stats() == []


@pytest.mark.asyncio
async def test_reporting_errors_do_not_break_httpx_calls(provider, monkeypatch):
    break_reporting(monkeypatch)
    url = provider + "/v1/chat/completions"
    assert httpx.post(url, json={}).json()["model"] == "gpt-4o-mini-2024-07-18"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json={})
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"
