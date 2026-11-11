import http.server
import json
import os
import threading

import pytest
import aikido_zen.sinks.mistralai

from aikido_zen.thread.thread_cache import get_cache

skip_no_api_key = pytest.mark.skipif(
    "MISTRAL_API_KEY" not in os.environ,
    reason="MISTRAL_API_KEY environment variable not set",
)


@pytest.fixture(autouse=True)
def setup():
    get_cache().reset()
    yield
    get_cache().reset()


def create_client(**kwargs):
    pytest.importorskip("mistralai")
    try:
        from mistralai.client import Mistral
    except ImportError:
        from mistralai import Mistral

    return Mistral(**kwargs)


@pytest.fixture
def mistral():
    return create_client(api_key=os.getenv("MISTRAL_API_KEY", ""))


class FakeMistralHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        reply = {
            "id": "1",
            "object": "list",
            "model": body.get("model", "mistral-medium-latest"),
            "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
        }
        if self.path == "/v1/embeddings":
            reply["data"] = [{"object": "embedding", "embedding": [0.1], "index": 0}]
        else:
            reply["created"] = 1
            reply["choices"] = [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": "Hi"},
                }
            ]
        data = json.dumps(reply).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture
def fake_mistral():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FakeMistralHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield create_client(
        api_key="test", server_url=f"http://127.0.0.1:{server.server_port}"
    )
    server.shutdown()
    server.server_close()


def get_ai_stats():
    return get_cache().ai_stats.get_stats()


MESSAGES = [{"role": "user", "content": "Hi"}]


@pytest.mark.parametrize(
    "resource, method, kwargs, model",
    [
        (
            "chat",
            "complete",
            {"model": "mistral-small-latest", "messages": MESSAGES},
            "mistral-small-latest",
        ),
        (
            "agents",
            "complete",
            {"agent_id": "ag-1", "messages": MESSAGES},
            "mistral-medium-latest",
        ),
        (
            "embeddings",
            "create",
            {"model": "mistral-embed", "inputs": ["Hi"]},
            "mistral-embed",
        ),
        (
            "fim",
            "complete",
            {"model": "codestral-latest", "prompt": "def"},
            "codestral-latest",
        ),
    ],
)
def test_each_call_is_counted_once(fake_mistral, resource, method, kwargs, model):
    call = getattr(getattr(fake_mistral, resource), method)
    call(**kwargs)
    call(**kwargs)

    assert get_ai_stats() == [
        {
            "provider": "mistralai",
            "model": model,
            "calls": 2,
            "tokens": {"input": 22, "output": 14, "total": 36},
        }
    ]


@skip_no_api_key
def test_mistralai_chat_complete(mistral):
    response = mistral.chat.complete(
        model="mistral-small-latest",  # Specify the Mistralai model
        max_tokens=20,
        messages=[
            {
                "role": "user",
                "content": "Write the longest response possible, just as I am writing a long content",
            }
        ],
    )
    print(response)

    assert get_ai_stats()[0]["model"] == "mistral-small-latest"
    assert get_ai_stats()[0]["calls"] == 1
    assert get_ai_stats()[0]["provider"] == "mistralai"
    assert get_ai_stats()[0]["tokens"]["input"] == 17
    assert get_ai_stats()[0]["tokens"]["output"] == 20
    assert get_ai_stats()[0]["tokens"]["total"] == 37


@skip_no_api_key
def test_mistralai_agents_complete(mistral):
    res = mistral.agents.complete(
        max_tokens=11,
        messages=[
            {
                "content": "Who is the best French painter? Answer in one short sentence.",
                "role": "user",
            },
        ],
        agent_id="ag:e1521cc4:20250805:untitled-agent:498e0dd8",
    )
    print(res)

    assert get_ai_stats()[0]["model"] == "mistral-medium-latest"
    assert get_ai_stats()[0]["calls"] == 1
    assert get_ai_stats()[0]["provider"] == "mistralai"
    assert get_ai_stats()[0]["tokens"]["input"] == 16
    assert get_ai_stats()[0]["tokens"]["output"] == 11
    assert get_ai_stats()[0]["tokens"]["total"] == 27


@skip_no_api_key
def test_mistralai_embeddings_create(mistral):
    res = mistral.embeddings.create(
        model="mistral-embed",
        inputs=[
            "Embed this sentence.",
            "As well as this one.",
        ],
    )
    print(res)

    assert get_ai_stats()[0]["model"] == "mistral-embed"
    assert get_ai_stats()[0]["calls"] == 1
    assert get_ai_stats()[0]["provider"] == "mistralai"
    assert get_ai_stats()[0]["tokens"]["input"] == 15
    assert get_ai_stats()[0]["tokens"]["output"] == 0  # Double-checked this
    assert get_ai_stats()[0]["tokens"]["total"] == 15


@skip_no_api_key
def test_mistralai_fim_complete(mistral):
    res = mistral.fim.complete(
        model="codestral-2405", prompt="def", suffix="return a+b", max_tokens=6
    )
    print(res)

    assert get_ai_stats()[0]["model"] == "codestral-2405"
    assert get_ai_stats()[0]["calls"] == 1
    assert get_ai_stats()[0]["provider"] == "mistralai"
    assert get_ai_stats()[0]["tokens"]["input"] == 8
    assert get_ai_stats()[0]["tokens"]["output"] == 6
    assert get_ai_stats()[0]["tokens"]["total"] == 14
