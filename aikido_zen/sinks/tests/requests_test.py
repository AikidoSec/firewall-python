import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import aikido_zen.sinks.requests
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
    enable_capture(aikido_zen.sinks.requests)


@pytest.fixture(scope="module")
def provider():
    with serve_provider() as url:
        yield url


@pytest.fixture(autouse=True)
def setup():
    get_cache().reset()
    yield
    get_cache().reset()


def test_requests_counts_once_and_body_stays_readable(provider):
    response = requests.post(provider + "/v1/chat/completions", json={})
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"
    assert_counted_once(provider, "gpt-4o-mini-2024-07-18", 11, 7)


def test_requests_gzip_body_is_parsed(provider):
    response = requests.post(provider + "/v1/chat/completions?gzip", json={})
    assert response.headers["Content-Encoding"] == "gzip"
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"
    assert_counted_once(provider, "gpt-4o-mini-2024-07-18", 11, 7)


def test_plain_requests_calls_are_unchanged(provider):
    url = provider + "/api/orders"
    for response in (requests.get(url), requests.post(url, json={"order": 1})):
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/json"
        assert response.json() == ORDER
    assert get_ai_stats() == []


def test_requests_stream_is_not_read_and_not_counted(provider):
    response = requests.post(
        provider + "/v1/chat/completions", json={"stream": True}, stream=True
    )
    assert response._content is False
    assert b"[DONE]" in b"".join(response.iter_content(1024))
    assert get_ai_stats() == []


def test_requests_redirect_counts_once(provider):
    response = requests.post(provider + "/redirect/v1/chat/completions", json={})
    assert response.history[0].status_code == 307
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"
    assert_counted_once(provider, "gpt-4o-mini-2024-07-18", 11, 7)


def test_requests_retry_counts_once(provider):
    retry = Retry(total=1, status_forcelist=[503], allowed_methods=None)
    with requests.Session() as session:
        session.mount("http://", HTTPAdapter(max_retries=retry))
        response = session.post(provider + "/v1/chat/completions?fail_once", json={})
    assert [error.status for error in response.raw.retries.history] == [503]
    assert response.status_code == 200
    assert_counted_once(provider, "gpt-4o-mini-2024-07-18", 11, 7)


def test_requests_errors_still_reach_the_app():
    with pytest.raises(requests.ConnectionError):
        requests.post(unreachable_url("/v1/chat/completions"), json={})
    assert get_ai_stats() == []


def test_reporting_errors_do_not_break_requests_calls(provider, monkeypatch):
    break_reporting(monkeypatch)
    response = requests.post(provider + "/v1/chat/completions", json={})
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"


def test_requests_only_parses_the_url_of_a_read_post(provider, monkeypatch):
    split = []
    real_urlsplit = aikido_zen.sinks.requests.urlsplit
    monkeypatch.setattr(
        aikido_zen.sinks.requests,
        "urlsplit",
        lambda url: split.append(url) or real_urlsplit(url),
    )
    requests.get(provider + "/v1/chat/completions")
    requests.post(
        provider + "/v1/chat/completions", json={"stream": True}, stream=True
    ).close()
    assert split == []
    requests.post(provider + "/v1/chat/completions", json={})
    assert split == [provider + "/v1/chat/completions"]
