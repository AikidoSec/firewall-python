import gzip
import itertools
import json
import os
import pathlib
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from urllib.parse import parse_qs, quote, unquote

import pytest
import httpx
import requests
import urllib3
import urllib3.connectionpool

try:
    import httpx2
except ImportError:
    httpx2 = None

import aikido_zen
import aikido_zen.helpers.ai_network_capture
import aikido_zen.sinks.httpx
import aikido_zen.sinks.httpx2
import aikido_zen.sinks.requests
import aikido_zen.sinks.urllib3
import aikido_zen.sinks.openai
import aikido_zen.sinks.anthropic
import aikido_zen.sinks.botocore
from aikido_zen.helpers.ai_network_capture import is_ai_network_capture_enabled
from aikido_zen.sinks import patch_function
from aikido_zen.thread.thread_cache import get_cache

skip_no_httpx2 = pytest.mark.skipif(httpx2 is None, reason="httpx2 not installed")

HELLO = [{"role": "user", "content": "Hi"}]
BEDROCK_MODEL = "anthropic.claude-haiku-4-5-20251001-v1:0"
INFERENCE_PROFILE_ARN = (
    "arn:aws:bedrock:us-east-1:1:inference-profile/us.anthropic.claude"
)
CHAT_COMPLETION = {
    "id": "chatcmpl-1",
    "object": "chat.completion",
    "created": 1,
    "model": "gpt-4o-mini-2024-07-18",
    "choices": [
        {
            "index": 0,
            "finish_reason": "stop",
            "message": {"role": "assistant", "content": "Hi"},
        }
    ],
    "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
}
RESPONSE = {
    "id": "resp_1",
    "object": "response",
    "model": "gpt-4o-2024-08-06",
    "output": [],
    "usage": {"input_tokens": 20, "output_tokens": 9, "total_tokens": 29},
}
MESSAGE = {
    "id": "msg_1",
    "type": "message",
    "role": "assistant",
    "model": "claude-sonnet-4-20250514",
    "content": [{"type": "text", "text": "Hi"}],
    "usage": {"input_tokens": 21, "output_tokens": 12},
}
GEMINI = {
    "candidates": [{"content": {"role": "model", "parts": [{"text": "Hi"}]}}],
    "usageMetadata": {"promptTokenCount": 70, "candidatesTokenCount": 8},
    "modelVersion": "gemini-2.5-flash-001",
}
SSE_BODY = (
    b'data: {"id":"chatcmpl-1","object":"chat.completion.chunk","model":"gpt-4o-mini",'
    b'"choices":[{"index":0,"delta":{"content":"Hi"}}]}\n\n'
    b"data: [DONE]\n\n"
)
BODIES = {
    "/v1/chat/completions": CHAT_COMPLETION,
    "/v1/responses": RESPONSE,
    "/v1/messages": MESSAGE,
    "/v1/plain": CHAT_COMPLETION,
    "/openai/v1/chat/completions": CHAT_COMPLETION,
    "/openai/deployments/gpt-4o-mini/chat/completions": CHAT_COMPLETION,
    "/v1beta/models/gemini-2.5-flash:generateContent": GEMINI,
    "/model/" + BEDROCK_MODEL + "/invoke": MESSAGE,
    "/model/" + INFERENCE_PROFILE_ARN + "/invoke": MESSAGE,
}
RESPONSE_IDS = itertools.count()


class ProviderHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self.do_POST()

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        request = json.loads(self.rfile.read(length) or b"{}")
        path, _, query = self.path.partition("?")
        path = unquote(path)
        options = parse_qs(query, keep_blank_values=True)

        if query == "not-json":
            return self.send_json_bytes(b"not json {")
        if path == "/v1/redirect":
            self.send_response(307)
            self.send_header("Location", "/v1/chat/completions")
            self.end_headers()
            return None
        if request.get("bad_key"):
            return self.send_json_bytes(
                b'{"error": {"message": "Incorrect API key"}}', status=401
            )
        if request.get("stream"):
            return self.send_sse()
        body = BODIES.get(path)
        if body is None:
            self.send_response(404)
            self.end_headers()
            return None
        if "id" in body:
            body = {**body, "id": body["id"] + "-" + str(next(RESPONSE_IDS))}
        if "pad" in options:
            body = {**body, "pad": "x" * int(options["pad"][0])}
        data = json.dumps(body).encode()
        if query == "gzip":
            return self.send_json_bytes(gzip.compress(data), encoding="gzip")
        status = int(options["status"][0]) if "status" in options else 200
        return self.send_json_bytes(data, status=status)

    def send_json_bytes(self, data, encoding=None, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        if encoding:
            self.send_header("Content-Encoding", encoding)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(SSE_BODY)))
        self.end_headers()
        self.wfile.write(SSE_BODY)


@pytest.fixture(scope="module", autouse=True)
def patch_http_clients_without_the_flag():
    if not is_ai_network_capture_enabled():
        aikido_zen.sinks.httpx.patch_client(httpx)
        if httpx2 is not None:
            aikido_zen.sinks.httpx.patch_client(httpx2)
        patch_function(requests, "Session.send", aikido_zen.sinks.requests._send)
        patch_function(
            urllib3.connectionpool,
            "HTTPConnectionPool.urlopen",
            aikido_zen.sinks.urllib3._urlopen,
        )


@pytest.fixture(scope="module")
def provider():
    server = ThreadingHTTPServer(("127.0.0.1", 0), ProviderHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield "http://127.0.0.1:%d" % server.server_address[1]
    server.shutdown()


@pytest.fixture(autouse=True)
def setup(provider):
    get_cache().reset()
    yield
    get_cache().reset()


def get_ai_stats():
    return get_cache().ai_stats.get_stats()


def stats_row(url, model, input_tokens, output_tokens):
    return {
        "provider": url,
        "model": model,
        "calls": 1,
        "tokens": {
            "input": input_tokens,
            "output": output_tokens,
            "total": input_tokens + output_tokens,
        },
    }


def assert_counted_once(url, model, input_tokens, output_tokens):
    assert get_ai_stats() == [stats_row(url, model, input_tokens, output_tokens)]


def test_requests_counts_once_and_body_stays_readable(provider):
    response = requests.post(provider + "/v1/chat/completions", json={})
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"
    assert_counted_once(
        provider + "/v1/chat/completions", "gpt-4o-mini-2024-07-18", 11, 7
    )


def test_requests_gzip_body_is_parsed(provider):
    response = requests.post(provider + "/v1/chat/completions?gzip", json={})
    assert response.headers["Content-Encoding"] == "gzip"
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"
    assert_counted_once(
        provider + "/v1/chat/completions", "gpt-4o-mini-2024-07-18", 11, 7
    )


def test_httpx_counts_once_and_body_stays_readable(provider):
    with httpx.Client() as client:
        response = client.post(provider + "/v1/responses", json={})
    assert response.json()["model"] == "gpt-4o-2024-08-06"
    assert_counted_once(provider + "/v1/responses", "gpt-4o-2024-08-06", 20, 9)


@skip_no_httpx2
def test_httpx2_counts_once_and_body_stays_readable(provider):
    with httpx2.Client() as client:
        response = client.post(provider + "/v1/messages", json={})
    assert response.json()["model"] == "claude-sonnet-4-20250514"
    assert_counted_once(provider + "/v1/messages", "claude-sonnet-4-20250514", 21, 12)


def test_urllib3_counts_once_and_body_stays_readable(provider):
    response = urllib3.PoolManager().request(
        "POST", provider + "/v1/chat/completions?gzip", body=b"{}"
    )
    assert response.headers["Content-Encoding"] == "gzip"
    assert json.loads(response.data)["model"] == "gpt-4o-mini-2024-07-18"
    assert_counted_once(
        provider + "/v1/chat/completions", "gpt-4o-mini-2024-07-18", 11, 7
    )


@pytest.mark.asyncio
async def test_httpx_async_counts_once(provider):
    async with httpx.AsyncClient() as client:
        response = await client.post(provider + "/v1/chat/completions", json={})
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"
    assert_counted_once(
        provider + "/v1/chat/completions", "gpt-4o-mini-2024-07-18", 11, 7
    )


@skip_no_httpx2
@pytest.mark.asyncio
async def test_httpx2_async_counts_once(provider):
    async with httpx2.AsyncClient() as client:
        response = await client.post(provider + "/v1/chat/completions", json={})
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"
    assert_counted_once(
        provider + "/v1/chat/completions", "gpt-4o-mini-2024-07-18", 11, 7
    )


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
def test_ai_path_is_counted_under_its_url_without_the_query(provider, path, expected):
    requests.post(provider + path, json={})
    assert_counted_once(provider + path.partition("?")[0], *expected)


def test_http_clients_report_the_same_url_for_an_encoded_path(provider):
    path = "/model/" + quote(INFERENCE_PROFILE_ARN, safe="") + "/invoke"
    requests.post(provider + path, json={})
    with httpx.Client() as client:
        client.post(provider + path, json={})
    urllib3.PoolManager().request("POST", provider + path, body=b"{}")
    assert [(s["provider"], s["model"], s["calls"]) for s in get_ai_stats()] == [
        (provider + path, "claude-sonnet-4-20250514", 3)
    ]


def test_reported_url_has_no_user_info_query_or_fragment(provider):
    url = provider.replace("http://", "http://user:secret@")
    requests.post(url + "/v1/chat/completions?key=secret#top", json={})
    with httpx.Client() as client:
        client.post(url + "/v1/chat/completions?key=secret", json={})
    assert [(s["provider"], s["calls"]) for s in get_ai_stats()] == [
        (provider + "/v1/chat/completions", 2)
    ]


@pytest.mark.parametrize(
    "method, path", [("GET", "/v1/responses"), ("POST", "/v1/plain")]
)
def test_other_requests_are_not_counted(provider, method, path):
    requests.request(method, provider + path, json={})
    with httpx.Client() as client:
        client.request(method, provider + path, json={})
    assert get_ai_stats() == []


def test_redirected_response_counts_once(provider):
    response = requests.post(provider + "/v1/redirect", json={})
    assert response.history[0].status_code == 307
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"
    with httpx.Client(follow_redirects=True) as client:
        response = client.post(provider + "/v1/redirect", json={})
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"
    assert get_ai_stats()[0]["calls"] == 2


def test_requests_stream_is_not_read_and_not_counted(provider):
    response = requests.post(
        provider + "/v1/chat/completions", json={"stream": True}, stream=True
    )
    assert response._content is False
    assert b"[DONE]" in b"".join(response.iter_content(1024))
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


def test_body_is_only_parsed_after_method_and_path_match(provider, monkeypatch):
    parsed = []
    monkeypatch.setattr(
        aikido_zen.helpers.ai_network_capture,
        "json",
        SimpleNamespace(loads=lambda body: parsed.append(body)),
    )
    with httpx.Client() as client:
        client.post(provider + "/v1/plain", json={})
        client.get(provider + "/v1/chat/completions")
        assert parsed == []
        client.post(provider + "/v1/chat/completions", json={})
        assert len(parsed) == 1
    urllib3.PoolManager().request("GET", provider + "/v1/chat/completions")
    assert len(parsed) == 1


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


def test_large_response_is_counted(provider):
    requests.post(provider + "/v1/chat/completions?pad=9000000", json={})
    assert_counted_once(
        provider + "/v1/chat/completions", "gpt-4o-mini-2024-07-18", 11, 7
    )


def test_error_responses_are_not_counted(provider):
    assert (
        requests.post(provider + "/v1/chat/completions?status=503").status_code == 503
    )
    response = requests.post(provider + "/v1/chat/completions", json={"bad_key": 1})
    assert response.status_code == 401
    with httpx.Client() as client:
        client.post(provider + "/v1/chat/completions?status=503", json={})
    urllib3.PoolManager().request(
        "POST", provider + "/v1/chat/completions?status=503", body=b"{}"
    )
    assert get_ai_stats() == []


def test_invalid_json_is_swallowed(provider):
    response = requests.post(provider + "/v1/chat/completions?not-json", json={})
    assert response.content == b"not json {"
    with httpx.Client() as client:
        response = client.post(provider + "/v1/chat/completions?not-json", json={})
    assert response.content == b"not json {"
    assert get_ai_stats() == []


def test_openai_sdk_call_is_counted_by_http_alongside_the_sdk_sink(provider):
    import openai

    client = openai.OpenAI(api_key="test", base_url=provider + "/v1", max_retries=0)
    client.chat.completions.create(model="gpt-4o-mini", messages=HELLO)
    assert get_ai_stats() == [
        stats_row(provider + "/v1/chat/completions", "gpt-4o-mini-2024-07-18", 11, 7),
        stats_row("openai", "gpt-4o-mini-2024-07-18", 11, 7),
    ]


def test_anthropic_sdk_call_is_counted_by_http_alongside_the_sdk_sink(provider):
    import anthropic

    client = anthropic.Anthropic(api_key="test", base_url=provider, max_retries=0)
    client.messages.create(model="claude-sonnet-4", max_tokens=5, messages=HELLO)
    assert get_ai_stats() == [
        stats_row(provider + "/v1/messages", "claude-sonnet-4-20250514", 21, 12),
        stats_row("anthropic", "claude-sonnet-4-20250514", 21, 12),
    ]


def test_boto3_bedrock_call_is_counted_by_the_botocore_sink_only(provider):
    boto3 = pytest.importorskip("boto3")
    client = boto3.client(
        "bedrock-runtime",
        region_name="us-east-1",
        endpoint_url=provider,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    response = client.invoke_model(
        modelId=BEDROCK_MODEL,
        body=json.dumps({"messages": HELLO}),
    )
    assert json.loads(response["body"].read())["model"] == "claude-sonnet-4-20250514"
    assert get_ai_stats() == [stats_row("bedrock", BEDROCK_MODEL, 0, 0)]


@pytest.mark.parametrize("flag, patched", [(None, False), ("true", True)])
def test_http_clients_are_only_patched_with_the_flag(flag, patched):
    env = {
        k: v for k, v in os.environ.items() if k != "AIKIDO_FEATURE_AI_NETWORK_CAPTURE"
    }
    if flag:
        env["AIKIDO_FEATURE_AI_NETWORK_CAPTURE"] = flag
    env["PYTHONPATH"] = str(pathlib.Path(aikido_zen.__file__).parents[1])
    code = (
        "import httpx, requests, urllib3.connectionpool\n"
        "import aikido_zen.sinks.httpx, aikido_zen.sinks.requests\n"
        "import aikido_zen.sinks.urllib3\n"
        "targets = [httpx.Client.send, httpx.AsyncClient.send, requests.Session.send,\n"
        "           urllib3.connectionpool.HTTPConnectionPool.urlopen]\n"
        "print([hasattr(t, '__wrapped__') for t in targets])\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == str([patched] * 4)
