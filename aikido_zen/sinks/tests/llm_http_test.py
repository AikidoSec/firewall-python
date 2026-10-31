import gzip
import itertools
import json
import threading
import time
from urllib.parse import parse_qs
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import pytest
import httpx
import requests
import urllib3

try:
    import httpx2
except ImportError:
    httpx2 = None

import aikido_zen.sinks.httpx
import aikido_zen.sinks.httpx2
import aikido_zen.sinks.requests
import aikido_zen.sinks.urllib3
import aikido_zen.helpers.inspect_llm_response
from aikido_zen.helpers.ai_provider_hosts import PROVIDER_BY_HOST
from aikido_zen.thread.thread_cache import get_cache

skip_no_httpx2 = pytest.mark.skipif(httpx2 is None, reason="httpx2 not installed")

CHAT_COMPLETION = {
    "id": "chatcmpl-1",
    "object": "chat.completion",
    "created": 1,
    "model": "gpt-4o-mini-2024-07-18",
    "choices": [
        {
            "index": 0,
            "finish_reason": "tool_calls",
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "read_file",
                            "arguments": '{"path": "/etc/passwd"}',
                        },
                    }
                ],
            },
        }
    ],
    "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
}

RESPONSE = {
    "id": "resp_1",
    "object": "response",
    "model": "gpt-4o-2024-08-06",
    "output": [
        {
            "type": "function_call",
            "call_id": "call_2",
            "name": "run_shell",
            "arguments": '{"command": "cat ~/.ssh/id_rsa"}',
        }
    ],
    "usage": {"input_tokens": 20, "output_tokens": 9, "total_tokens": 29},
}

MESSAGE = {
    "id": "msg_1",
    "type": "message",
    "role": "assistant",
    "model": "claude-sonnet-4-20250514",
    "stop_reason": "tool_use",
    "content": [
        {"type": "text", "text": "Reading it now."},
        {
            "type": "tool_use",
            "id": "toolu_1",
            "name": "read_file",
            "input": {"path": "/etc/shadow"},
        },
    ],
    "usage": {"input_tokens": 21, "output_tokens": 12},
}

SSE_BODY = (
    b'data: {"id":"chatcmpl-1","object":"chat.completion.chunk","model":"gpt-4o-mini",'
    b'"choices":[{"index":0,"delta":{"role":"assistant","tool_calls":[{"index":0,'
    b'"function":{"name":"read_file","arguments":"{\\"path\\": \\"/etc/passwd\\"}"}}]}}]}\n\n'
    b'data: {"id":"chatcmpl-1","object":"chat.completion.chunk","model":"gpt-4o-mini",'
    b'"choices":[{"index":0,"delta":{},"finish_reason":"tool_calls"}],'
    b'"usage":{"prompt_tokens":11,"completion_tokens":7,"total_tokens":18}}\n\n'
    b"data: [DONE]\n\n"
)

GEMINI = {
    "candidates": [
        {
            "content": {
                "role": "model",
                "parts": [{"functionCall": {"name": "get_weather", "args": {}}}],
            }
        }
    ],
    "usageMetadata": {
        "promptTokenCount": 70,
        "toolUsePromptTokenCount": 30,
        "candidatesTokenCount": 8,
        "thoughtsTokenCount": 500,
    },
    "modelVersion": "gemini-2.5-flash-001",
}

EMBEDDINGS = {
    "id": "embd-1",
    "object": "list",
    "model": "mistral-embed",
    "data": [{"object": "embedding", "index": 0, "embedding": [0.1]}],
    "usage": {"prompt_tokens": 15, "completion_tokens": 0, "total_tokens": 15},
}

RESPONSE_IDS = itertools.count()
FAILED_ONCE = set()


BODIES = {
    "/v1/chat/completions": CHAT_COMPLETION,
    "/v1/responses": RESPONSE,
    "/v1/messages": MESSAGE,
    "/v1/embeddings": EMBEDDINGS,
    "/v1/agents/completions": CHAT_COMPLETION,
    "/v1/fim/completions": CHAT_COMPLETION,
    "/openai/v1/chat/completions": CHAT_COMPLETION,
    "/openai/v1/responses": RESPONSE,
    "/openai/deployments/gpt-4o-mini/chat/completions": CHAT_COMPLETION,
    "/anthropic/v1/messages": MESSAGE,
    "/v1beta/models/gemini-2.5-flash:generateContent": GEMINI,
    "/v1/messages/count_tokens": MESSAGE,
    "/v1/plain": CHAT_COMPLETION,
}


class ProviderHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self.do_POST()

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        request = json.loads(self.rfile.read(length) or b"{}")
        path, _, query = self.path.partition("?")
        options = parse_qs(query, keep_blank_values=True)

        if "delay" in options:
            time.sleep(float(options["delay"][0]))
        if "fail-once" in options and options["fail-once"][0] not in FAILED_ONCE:
            FAILED_ONCE.add(options["fail-once"][0])
            return self.send_json_bytes(b'{"error": {"message": "boom"}}', status=500)
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
        for field in ("usage", "id"):
            if "no-" + field in options:
                body = {k: v for k, v in body.items() if k != field}
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


@pytest.fixture(scope="module")
def provider():
    server = ThreadingHTTPServer(("127.0.0.1", 0), ProviderHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield "http://127.0.0.1:%d" % server.server_address[1]
    server.shutdown()


@pytest.fixture(autouse=True)
def setup(monkeypatch, provider):
    monkeypatch.setitem(PROVIDER_BY_HOST, "127.0.0.1", "openai")
    get_cache().reset()
    yield
    get_cache().reset()


def get_ai_stats():
    return get_cache().ai_stats.get_stats()


def get_ai_operations():
    operations = get_cache().stats.get_record()["operations"]
    return sorted(op for op, stats in operations.items() if stats["kind"] == "ai_op")


def assert_counted_once(model, input_tokens, output_tokens, provider_name="openai"):
    stats = get_ai_stats()
    assert len(stats) == 1
    assert stats[0]["provider"] == provider_name
    assert stats[0]["model"] == model
    assert stats[0]["calls"] == 1
    assert stats[0]["tokens"]["input"] == input_tokens
    assert stats[0]["tokens"]["output"] == output_tokens


def test_requests_counts_once_and_body_stays_readable(provider):
    response = requests.post(provider + "/v1/chat/completions", json={})
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"
    assert_counted_once("gpt-4o-mini-2024-07-18", 11, 7)
    assert get_ai_operations() == ["requests.Session.send"]


def test_requests_gzip_body_is_parsed(provider):
    response = requests.post(provider + "/v1/chat/completions?gzip", json={})
    assert response.headers["Content-Encoding"] == "gzip"
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"
    assert_counted_once("gpt-4o-mini-2024-07-18", 11, 7)


def test_httpx_counts_once_and_body_stays_readable(provider):
    with httpx.Client() as client:
        response = client.post(provider + "/v1/responses", json={})
    assert response.json()["model"] == "gpt-4o-2024-08-06"
    assert_counted_once("gpt-4o-2024-08-06", 20, 9)


@skip_no_httpx2
def test_httpx2_counts_once_and_body_stays_readable(provider, monkeypatch):
    monkeypatch.setitem(PROVIDER_BY_HOST, "127.0.0.1", "anthropic")
    with httpx2.Client() as client:
        response = client.post(provider + "/v1/messages", json={})
    assert response.json()["model"] == "claude-sonnet-4-20250514"
    assert_counted_once("claude-sonnet-4-20250514", 21, 12, "anthropic")
    assert get_ai_operations() == ["httpx2.Client.send"]


@pytest.mark.parametrize(
    "path, expected",
    [
        ("/v1/agents/completions", ("gpt-4o-mini-2024-07-18", 11, 7)),
        ("/v1/fim/completions", ("gpt-4o-mini-2024-07-18", 11, 7)),
        ("/v1/embeddings", ("mistral-embed", 15, 0)),
    ],
)
def test_mistral_paths_count_on_mistral_host_only(
    provider, monkeypatch, path, expected
):
    requests.post(provider + path, json={})
    assert get_ai_stats() == []
    monkeypatch.setitem(PROVIDER_BY_HOST, "127.0.0.1", "mistral")
    requests.post(provider + path, json={})
    assert_counted_once(*expected, "mistral")


@pytest.mark.parametrize(
    "path, expected",
    [
        (
            "/v1/chat/completions",
            ("gpt-4o-mini-2024-07-18", 11, 7, "openai_compatible"),
        ),
        (
            "/openai/v1/chat/completions",
            ("gpt-4o-mini-2024-07-18", 11, 7, "openai_compatible"),
        ),
        ("/openai/v1/responses", ("gpt-4o-2024-08-06", 20, 9, "openai_compatible")),
        (
            "/openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-10-21",
            ("gpt-4o-mini-2024-07-18", 11, 7, "openai_compatible"),
        ),
        (
            "/anthropic/v1/messages",
            ("claude-sonnet-4-20250514", 21, 12, "anthropic_compatible"),
        ),
        (
            "/v1beta/models/gemini-2.5-flash:generateContent?key=secret",
            ("gemini-2.5-flash-001", 100, 508, "gemini_compatible"),
        ),
    ],
)
def test_ai_path_on_any_host_is_counted(provider, monkeypatch, path, expected):
    monkeypatch.delitem(PROVIDER_BY_HOST, "127.0.0.1")
    requests.post(provider + path, json={})
    assert_counted_once(*expected)


@pytest.mark.parametrize(
    "host, provider_name",
    [
        ("api.groq.com", "groq"),
        ("api.mistral.ai", "mistral"),
        ("api.anthropic.com", "anthropic"),
        ("generativelanguage.googleapis.com", "gemini"),
    ],
)
def test_known_host_names_the_provider(provider, monkeypatch, host, provider_name):
    monkeypatch.setitem(PROVIDER_BY_HOST, "127.0.0.1", PROVIDER_BY_HOST[host])
    requests.post(provider + "/openai/v1/responses", json={})
    assert_counted_once("gpt-4o-2024-08-06", 20, 9, provider_name)


def test_gemini_model_falls_back_to_the_path(provider, monkeypatch):
    monkeypatch.setitem(
        BODIES,
        "/v1beta/models/gemini-2.5-flash:generateContent",
        {k: v for k, v in GEMINI.items() if k != "modelVersion"},
    )
    requests.post(provider + "/v1beta/models/gemini-2.5-flash:generateContent", json={})
    assert_counted_once("gemini-2.5-flash", 100, 508)


@pytest.mark.parametrize(
    "method, path",
    [
        ("GET", "/v1/responses"),
        ("POST", "/v1/messages/count_tokens"),
        ("POST", "/v1/embeddings"),
        ("POST", "/v1/plain"),
    ],
)
def test_other_requests_are_not_parsed(provider, monkeypatch, method, path):
    parsed = []
    monkeypatch.setattr(
        aikido_zen.helpers.inspect_llm_response,
        "json",
        SimpleNamespace(loads=lambda body: parsed.append(body)),
    )
    response = requests.request(method, provider + path, json={})
    assert response.json()["model"]
    assert parsed == []
    assert get_ai_stats() == []


def test_urllib3_counts_once_and_body_stays_readable(provider):
    response = urllib3.PoolManager().request(
        "POST", provider + "/v1/chat/completions?gzip", body=b"{}"
    )
    assert response.headers["Content-Encoding"] == "gzip"
    assert json.loads(response.data)["model"] == "gpt-4o-mini-2024-07-18"
    assert_counted_once("gpt-4o-mini-2024-07-18", 11, 7)
    assert get_ai_operations() == ["urllib3.HTTPConnectionPool.urlopen"]


@pytest.mark.asyncio
async def test_httpx_async_counts_once(provider):
    async with httpx.AsyncClient() as client:
        response = await client.post(provider + "/v1/chat/completions", json={})
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"
    assert_counted_once("gpt-4o-mini-2024-07-18", 11, 7)


@skip_no_httpx2
@pytest.mark.asyncio
async def test_httpx2_async_counts_once(provider):
    async with httpx2.AsyncClient() as client:
        response = await client.post(provider + "/v1/chat/completions", json={})
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"
    assert_counted_once("gpt-4o-mini-2024-07-18", 11, 7)


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
    assert get_ai_stats() == []
    assert b"[DONE]" in b"".join(response.iter_content(1024))
    assert get_ai_stats() == []


def test_httpx_stream_is_not_read_and_not_counted(provider):
    with httpx.Client() as client:
        with client.stream(
            "POST", provider + "/v1/chat/completions", json={"stream": True}
        ) as response:
            with pytest.raises(httpx.ResponseNotRead):
                response.content
            assert get_ai_stats() == []
            assert b"[DONE]" in b"".join(response.iter_bytes())
    assert get_ai_stats() == []


@skip_no_httpx2
def test_httpx2_stream_is_not_read_and_not_counted(provider):
    with httpx2.Client() as client:
        with client.stream(
            "POST", provider + "/v1/chat/completions", json={"stream": True}
        ) as response:
            with pytest.raises(httpx2.ResponseNotRead):
                response.content
            assert get_ai_stats() == []
            assert b"[DONE]" in b"".join(response.iter_bytes())
    assert get_ai_stats() == []


def test_body_is_only_parsed_after_method_and_path_match(provider, monkeypatch):
    parsed = []
    monkeypatch.setattr(
        aikido_zen.helpers.inspect_llm_response,
        "json",
        SimpleNamespace(loads=lambda body: parsed.append(body)),
    )
    with httpx.Client() as client:
        client.post(provider + "/v1/embeddings", json={})
        client.get(provider + "/v1/chat/completions")
        assert parsed == []
        client.post(provider + "/v1/chat/completions", json={})
        assert len(parsed) == 1
    urllib3.PoolManager().request("GET", provider + "/v1/chat/completions")
    assert len(parsed) == 1


def test_large_response_is_counted(provider):
    requests.post(provider + "/v1/chat/completions?pad=9000000", json={})
    assert_counted_once("gpt-4o-mini-2024-07-18", 11, 7)


def test_error_status_with_a_valid_body_is_not_counted(provider):
    response = requests.post(provider + "/v1/chat/completions?status=503", json={})
    assert response.status_code == 503
    with httpx.Client() as client:
        client.post(provider + "/v1/chat/completions?status=503", json={})
    urllib3.PoolManager().request(
        "POST", provider + "/v1/chat/completions?status=503", body=b"{}"
    )
    assert get_ai_stats() == []


def test_error_body_is_not_counted(provider):
    response = requests.post(provider + "/v1/chat/completions", json={"bad_key": 1})
    assert response.status_code == 401
    assert get_ai_stats() == []
    assert get_ai_operations() == []


def test_invalid_json_is_swallowed(provider):
    response = requests.post(provider + "/v1/chat/completions?not-json", json={})
    assert response.content == b"not json {"
    with httpx.Client() as client:
        response = client.post(provider + "/v1/chat/completions?not-json", json={})
    assert response.content == b"not json {"
    assert get_ai_stats() == []


def test_body_without_the_api_shape_is_not_counted(provider, monkeypatch):
    monkeypatch.setitem(BODIES, "/v1/responses", CHAT_COMPLETION)
    requests.post(provider + "/v1/responses", json={})
    assert get_ai_stats() == []


def test_body_without_usage_is_not_counted(provider):
    response = requests.post(provider + "/v1/chat/completions?no-usage", json={})
    assert response.json()["model"] == "gpt-4o-mini-2024-07-18"
    assert get_ai_stats() == []
    assert get_ai_operations() == []
