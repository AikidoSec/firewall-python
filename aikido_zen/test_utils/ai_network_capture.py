import contextlib
import gzip
import importlib
import json
import pathlib
import socket
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote

import pytest

import aikido_zen
import aikido_zen.helpers.ai_network_capture
from aikido_zen.helpers.ai_network_capture import is_ai_network_capture_enabled
from aikido_zen.thread.thread_cache import get_cache

FLAG = "AIKIDO_FEATURE_AI_NETWORK_CAPTURE"
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
CHAT_COMPLETION_WITH_TOOLS = {
    **CHAT_COMPLETION,
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
                        "function": {"name": "search", "arguments": "{}"},
                    }
                ],
            },
        }
    ],
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
ORDER = {"order": 1, "items": ["a", "b"]}
BODIES = {
    "/api/orders": ORDER,
    "/v1/chat/completions": CHAT_COMPLETION,
    "/tools/v1/chat/completions": CHAT_COMPLETION_WITH_TOOLS,
    "/v1/responses": RESPONSE,
    "/v1/messages": MESSAGE,
    "/v1/plain": CHAT_COMPLETION,
    "/openai/v1/chat/completions": CHAT_COMPLETION,
    "/openai/deployments/gpt-4o-mini/chat/completions": CHAT_COMPLETION,
    "/v1beta/models/gemini-2.5-flash:generateContent": GEMINI,
    "/model/" + BEDROCK_MODEL + "/invoke": MESSAGE,
    "/model/" + INFERENCE_PROFILE_ARN + "/invoke": MESSAGE,
}
ENABLED_SINKS = set()


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
        if path == "/redirect/v1/chat/completions":
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
        if "pad" in options:
            body = {**body, "pad": "x" * int(options["pad"][0])}
        data = json.dumps(body).encode()
        if query == "gzip":
            return self.send_json_bytes(gzip.compress(data), encoding="gzip")
        status = int(options["status"][0]) if "status" in options else 200
        if "fail_once" in options and self.path not in self.server.failed_once:
            self.server.failed_once.add(self.path)
            status = 503
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


@contextlib.contextmanager
def serve_provider():
    server = ThreadingHTTPServer(("127.0.0.1", 0), ProviderHandler)
    server.failed_once = set()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def enable_capture(*sinks):
    """Patches the clients that are already imported, as the flag does at app start."""
    if is_ai_network_capture_enabled():
        return
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setenv(FLAG, "true")
        # A second reload would wrap the client methods twice.
        for sink in [sink for sink in sinks if sink not in ENABLED_SINKS]:
            importlib.reload(sink)
            ENABLED_SINKS.add(sink)


def run_in_protected_app(script, flag, *args):
    """Runs `script` after protect() in a new process, so the flag is read at import as
    in an app, and returns the JSON on the last line the script printed."""
    protect = 'import aikido_zen\n\naikido_zen.protect("daemon_disabled")\n'
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.delenv(FLAG, raising=False)
        if flag:
            monkeypatch.setenv(FLAG, flag)
        monkeypatch.setenv(
            "PYTHONPATH", str(pathlib.Path(aikido_zen.__file__).parents[1])
        )
        result = subprocess.run(
            [sys.executable, "-c", protect + script, *args],
            capture_output=True,
            text=True,
            check=True,
        )
    return json.loads(result.stdout.splitlines()[-1])


def unreachable_url(path):
    with socket.socket() as unused:
        unused.bind(("127.0.0.1", 0))
        return f"http://127.0.0.1:{unused.getsockname()[1]}{path}"


def break_reporting(monkeypatch):
    def fail(**kwargs):
        raise RuntimeError("reporting failed")

    monkeypatch.setattr(aikido_zen.helpers.ai_network_capture, "on_ai_call", fail)


def get_ai_stats():
    return get_cache().ai_stats.get_stats()


def get_tool_stats():
    return get_cache().ai_stats.get_tool_stats()


def stats_row(url, model, input_tokens, output_tokens):
    return {
        "provider": url,
        "model": model,
        "calls": 1,
        "tokens": {
            "input": input_tokens,
            "output": output_tokens,
            "total": input_tokens + output_tokens,
            "cacheRead": 0,
            "cacheWrite": 0,
        },
    }


def assert_counted_once(url, model, input_tokens, output_tokens):
    assert get_ai_stats() == [stats_row(url, model, input_tokens, output_tokens)]
