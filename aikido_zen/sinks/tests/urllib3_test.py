import json

import pytest
import urllib3
from urllib3.util.retry import Retry

import aikido_zen.sinks.urllib3
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
    enable_capture(aikido_zen.sinks.urllib3)


@pytest.fixture(scope="module")
def provider():
    with serve_provider() as url:
        yield url


@pytest.fixture(autouse=True)
def setup():
    get_cache().reset()
    yield
    get_cache().reset()


def test_urllib3_counts_once_and_body_stays_readable(provider):
    response = urllib3.PoolManager().request(
        "POST", provider + "/v1/chat/completions", body=b"{}"
    )
    assert json.loads(response.data)["model"] == "gpt-4o-mini-2024-07-18"
    assert_counted_once(
        provider + "/v1/chat/completions", "gpt-4o-mini-2024-07-18", 11, 7
    )


def test_urllib3_gzip_body_is_parsed(provider):
    response = urllib3.PoolManager().request(
        "POST", provider + "/v1/chat/completions?gzip", body=b"{}"
    )
    assert response.headers["Content-Encoding"] == "gzip"
    assert json.loads(response.data)["model"] == "gpt-4o-mini-2024-07-18"
    assert_counted_once(
        provider + "/v1/chat/completions", "gpt-4o-mini-2024-07-18", 11, 7
    )


def test_plain_urllib3_calls_are_unchanged(provider):
    http = urllib3.PoolManager()
    for response in (
        http.request("GET", provider + "/api/orders"),
        http.request("POST", provider + "/api/orders", body=b"{}"),
    ):
        assert response.status == 200
        assert response.headers["Content-Type"] == "application/json"
        assert json.loads(response.data) == ORDER
    assert get_ai_stats() == []


def test_urllib3_stream_is_not_read_and_not_counted(provider):
    response = urllib3.PoolManager().request(
        "POST",
        provider + "/v1/chat/completions",
        body=json.dumps({"stream": True}),
        preload_content=False,
    )
    assert b"[DONE]" in b"".join(response.stream(1024))
    assert get_ai_stats() == []


def test_urllib3_redirect_counts_once(provider):
    response = urllib3.PoolManager().request(
        "POST", provider + "/redirect/v1/chat/completions", body=b"{}"
    )
    assert json.loads(response.data)["model"] == "gpt-4o-mini-2024-07-18"
    assert_counted_once(
        provider + "/v1/chat/completions", "gpt-4o-mini-2024-07-18", 11, 7
    )


def test_urllib3_pool_redirect_counts_once(provider):
    pool = urllib3.connection_from_url(provider)
    response = pool.urlopen("POST", "/redirect/v1/chat/completions", body=b"{}")
    assert json.loads(response.data)["model"] == "gpt-4o-mini-2024-07-18"
    assert_counted_once(
        provider + "/v1/chat/completions", "gpt-4o-mini-2024-07-18", 11, 7
    )


def test_urllib3_retry_counts_once(provider):
    retry = Retry(total=1, status_forcelist=[503], allowed_methods=None)
    response = urllib3.PoolManager().request(
        "POST", provider + "/v1/chat/completions?fail_once", body=b"{}", retries=retry
    )
    assert [error.status for error in response.retries.history] == [503]
    assert response.status == 200
    assert_counted_once(
        provider + "/v1/chat/completions", "gpt-4o-mini-2024-07-18", 11, 7
    )


def test_urllib3_errors_still_reach_the_app():
    with pytest.raises(urllib3.exceptions.HTTPError):
        urllib3.PoolManager().request(
            "POST", unreachable_url("/v1/chat/completions"), body=b"{}", retries=False
        )
    assert get_ai_stats() == []


def test_reporting_errors_do_not_break_urllib3_calls(provider, monkeypatch):
    break_reporting(monkeypatch)
    response = urllib3.PoolManager().request(
        "POST", provider + "/v1/chat/completions", body=b"{}"
    )
    assert json.loads(response.data)["model"] == "gpt-4o-mini-2024-07-18"
