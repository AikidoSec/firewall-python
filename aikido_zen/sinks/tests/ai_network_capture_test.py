import json
from types import SimpleNamespace
from urllib.parse import quote

import anthropic
import httpx
import openai
import pytest
import requests
import urllib3

import aikido_zen.helpers.ai_network_capture
import aikido_zen.sinks.httpx
import aikido_zen.sinks.httpx2
import aikido_zen.sinks.requests
import aikido_zen.sinks.urllib3
import aikido_zen.sinks.openai
import aikido_zen.sinks.anthropic
import aikido_zen.sinks.botocore
from aikido_zen.test_utils.ai_network_capture import (
    BEDROCK_MODEL,
    FLAG,
    INFERENCE_PROFILE_ARN,
    assert_counted_once,
    enable_capture,
    get_ai_stats,
    get_tool_stats,
    run_in_protected_app,
    serve_provider,
    stats_row,
)
from aikido_zen.thread.thread_cache import get_cache

HELLO = [{"role": "user", "content": "Hi"}]


@pytest.fixture(scope="module", autouse=True)
def enable_the_flag():
    # Newer openai and anthropic versions send their calls through httpx2, which only
    # gets patched here if those SDKs have already imported it.
    enable_capture(
        aikido_zen.sinks.httpx,
        aikido_zen.sinks.httpx2,
        aikido_zen.sinks.requests,
        aikido_zen.sinks.urllib3,
    )


@pytest.fixture(scope="module")
def provider():
    with serve_provider() as url:
        yield url


@pytest.fixture(autouse=True)
def setup():
    get_cache().reset()
    yield
    get_cache().reset()


@pytest.mark.parametrize(
    "path, expected",
    [
        ("/openai/v1/chat/completions", ("gpt-4o-mini-2024-07-18", 11, 7)),
        (
            "/openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-10-21",
            ("gpt-4o-mini-2024-07-18", 11, 7),
        ),
        (
            "/v1beta/models/gemini-2.5-flash:generateContent?key=secret",
            ("gemini-2.5-flash-001", 70, 8),
        ),
    ],
)
def test_ai_path_is_counted_under_the_origin(provider, path, expected):
    requests.post(provider + path, json={})
    assert_counted_once(provider, *expected)


def test_http_clients_count_a_call_on_an_encoded_path_the_same_way(provider):
    path = "/model/" + quote(INFERENCE_PROFILE_ARN, safe="") + "/invoke"
    requests.post(provider + path, json={})
    httpx.post(provider + path, json={})
    urllib3.PoolManager().request("POST", provider + path, body=b"{}")
    assert [(s["provider"], s["model"], s["calls"]) for s in get_ai_stats()] == [
        (provider, "claude-sonnet-4-20250514", 3)
    ]


def test_reported_origin_has_no_user_info(provider):
    url = provider.replace("http://", "http://user:secret@")
    requests.post(url + "/v1/chat/completions?key=secret#top", json={})
    httpx.post(url + "/v1/chat/completions?key=secret", json={})
    urllib3.PoolManager().request(
        "POST", url + "/v1/chat/completions?key=secret", body=b"{}"
    )
    assert [(s["provider"], s["calls"]) for s in get_ai_stats()] == [(provider, 3)]


@pytest.mark.parametrize(
    "method, path", [("GET", "/v1/responses"), ("POST", "/v1/plain")]
)
def test_other_requests_are_not_counted(provider, method, path):
    requests.request(method, provider + path, json={})
    httpx.request(method, provider + path, json={})
    urllib3.PoolManager().request(method, provider + path, body=b"{}")
    assert get_ai_stats() == []


def test_error_responses_are_not_counted(provider):
    url = provider + "/v1/chat/completions?status=503"
    assert requests.post(url, json={}).status_code == 503
    assert httpx.post(url, json={}).status_code == 503
    assert urllib3.PoolManager().request("POST", url, body=b"{}").status == 503
    response = requests.post(provider + "/v1/chat/completions", json={"bad_key": 1})
    assert response.status_code == 401
    assert get_ai_stats() == []


def test_invalid_json_is_swallowed(provider):
    url = provider + "/v1/chat/completions?not-json"
    assert requests.post(url, json={}).content == b"not json {"
    assert httpx.post(url, json={}).content == b"not json {"
    assert urllib3.PoolManager().request("POST", url, body=b"{}").data == (
        b"not json {"
    )
    assert get_ai_stats() == []


def test_body_is_only_parsed_after_method_and_path_match(provider, monkeypatch):
    parsed = []
    monkeypatch.setattr(
        aikido_zen.helpers.ai_network_capture,
        "json",
        SimpleNamespace(loads=lambda body: parsed.append(body)),
    )
    for method, path in (("POST", "/v1/plain"), ("GET", "/v1/chat/completions")):
        requests.request(method, provider + path, json={})
        httpx.request(method, provider + path, json={})
        urllib3.PoolManager().request(method, provider + path, body=b"{}")
    assert parsed == []
    httpx.post(provider + "/v1/chat/completions", json={})
    assert len(parsed) == 1


@pytest.mark.parametrize("pad, counted", [(2_000_000, 1), (2_100_000, 0)])
def test_only_a_response_up_to_the_size_limit_is_counted(provider, pad, counted):
    response = requests.post(provider + f"/v1/chat/completions?pad={pad}", json={})
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"
    assert sum(s["calls"] for s in get_ai_stats()) == counted


def test_http_clients_report_tool_calls_under_the_origin(provider):
    url = provider + "/tools/v1/chat/completions"
    requests.post(url, json={})
    httpx.post(url, json={})
    urllib3.PoolManager().request("POST", url, body=b"{}")
    assert get_tool_stats() == [
        {
            "provider": provider,
            "model": "gpt-4o-mini-2024-07-18",
            "name": "search",
            "calls": 3,
        }
    ]


def test_openai_sdk_tool_calls_are_counted_once(provider):
    client = openai.OpenAI(
        api_key="test", base_url=provider + "/tools/v1", max_retries=0
    )
    response = client.chat.completions.create(model="gpt-4o-mini", messages=HELLO)
    assert response.choices[0].message.tool_calls[0].function.name == "search"
    assert get_tool_stats() == [
        {
            "provider": provider,
            "model": "gpt-4o-mini-2024-07-18",
            "name": "search",
            "calls": 1,
        }
    ]


def test_openai_sdk_call_is_counted_by_http_alongside_the_sdk_sink(provider):
    client = openai.OpenAI(api_key="test", base_url=provider + "/v1", max_retries=0)
    client.chat.completions.create(model="gpt-4o-mini", messages=HELLO)
    assert get_ai_stats() == [
        stats_row(provider, "gpt-4o-mini-2024-07-18", 11, 7),
        stats_row("openai", "gpt-4o-mini-2024-07-18", 11, 7),
    ]


def test_anthropic_sdk_call_is_counted_by_http_alongside_the_sdk_sink(provider):
    client = anthropic.Anthropic(api_key="test", base_url=provider, max_retries=0)
    client.messages.create(model="claude-sonnet-4", max_tokens=5, messages=HELLO)
    assert get_ai_stats() == [
        stats_row(provider, "claude-sonnet-4-20250514", 21, 12),
        stats_row("anthropic", "claude-sonnet-4-20250514", 21, 12),
    ]


@pytest.fixture
def bedrock(provider):
    boto3 = pytest.importorskip("boto3")
    return boto3.client(
        "bedrock-runtime",
        region_name="us-east-1",
        endpoint_url=provider,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )


def test_boto3_bedrock_call_is_counted_by_the_botocore_sink_only(bedrock):
    response = bedrock.invoke_model(
        modelId=BEDROCK_MODEL,
        body=json.dumps({"messages": HELLO}),
    )
    assert json.loads(response["body"].read())["model"] == "claude-sonnet-4-20250514"
    assert get_ai_stats() == [stats_row("bedrock", BEDROCK_MODEL, 0, 0)]


@pytest.mark.parametrize("flag, tools", [(None, []), ("true", ["get_weather"])])
def test_boto3_converse_tool_calls_are_counted_with_the_flag(
    bedrock, monkeypatch, flag, tools
):
    monkeypatch.delenv(FLAG, raising=False)
    if flag:
        monkeypatch.setenv(FLAG, flag)

    bedrock.converse(
        modelId=BEDROCK_MODEL, messages=[{"role": "user", "content": [{"text": "Hi"}]}]
    )

    assert get_ai_stats() == [stats_row("bedrock", BEDROCK_MODEL, 30, 12)]
    assert get_tool_stats() == [
        {"provider": "bedrock", "model": BEDROCK_MODEL, "name": name, "calls": 1}
        for name in tools
    ]


@pytest.mark.parametrize("flag, patched", [(None, False), ("true", True)])
def test_http_clients_are_only_patched_and_counted_with_the_flag(
    provider, flag, patched
):
    script = """
import json, sys
import httpx, requests, urllib3.connectionpool
from aikido_zen.thread.thread_cache import get_cache

url = sys.argv[1]
methods = [
    httpx.Client.send,
    httpx.AsyncClient.send,
    requests.Session.send,
    urllib3.connectionpool.HTTPConnectionPool.urlopen,
]
bodies = [
    requests.post(url, json={}).content,
    httpx.post(url, json={}).content,
    urllib3.PoolManager().request("POST", url, body=b"{}").data,
]
print(json.dumps({
    "wrapped": [hasattr(method, "__wrapped__") for method in methods],
    "models": [json.loads(body)["model"] for body in bodies],
    "calls": [stats["calls"] for stats in get_cache().ai_stats.get_stats()],
}))
"""
    output = run_in_protected_app(script, flag, provider + "/v1/chat/completions")
    assert output == {
        "wrapped": [patched] * 4,
        "models": ["gpt-4o-mini-2024-07-18"] * 3,
        "calls": [3] if patched else [],
    }
