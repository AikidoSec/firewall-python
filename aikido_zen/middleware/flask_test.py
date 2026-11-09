from unittest.mock import Mock, patch
from weakref import ref

import pytest
from werkzeug.test import create_environ
from werkzeug.wrappers import Request

from .flask import AikidoFlaskMiddleware


def call_middleware(result, environ=None):
    captured = {}
    if environ is None:
        environ = create_environ("/")

    def start_response(status, headers, exc_info=None):
        captured["status"] = status
        captured["headers"] = dict(headers)

    with patch("aikido_zen.middleware.flask.should_block_request", return_value=result):
        middleware = AikidoFlaskMiddleware(app=None)
        captured["body"] = b"".join(middleware(environ, start_response))
    return captured


def test_rate_limited_response_has_retry_after():
    response = call_middleware(
        {
            "block": True,
            "type": "ratelimited",
            "trigger": "ip",
            "ip": "1.1.1.1",
            "retry_after_seconds": 7,
        }
    )
    assert response["status"] == "429 TOO MANY REQUESTS"
    assert response["headers"]["Retry-After"] == "7"
    assert response["body"] == b"You are rate limited by Zen. (Your IP: 1.1.1.1)"


def test_rate_limited_response_without_retry_after_seconds():
    response = call_middleware(
        {
            "block": True,
            "type": "ratelimited",
            "trigger": "user",
            "ip": "1.1.1.1",
            "retry_after_seconds": None,
        }
    )
    assert response["status"] == "429 TOO MANY REQUESTS"
    assert "Retry-After" not in response["headers"]


@pytest.mark.parametrize("block_type", ["ratelimited", "blocked"])
def test_blocked_response_releases_outer_request(block_type):
    environ = create_environ("/")
    outer_request = Request(environ)
    request_ref = ref(outer_request)
    del outer_request

    response = call_middleware(
        {
            "block": True,
            "type": block_type,
            "trigger": "user",
            "retry_after_seconds": None,
        },
        environ,
    )

    assert response["status"].startswith(
        "429" if block_type == "ratelimited" else "403"
    )
    assert environ["werkzeug.request"] is None
    assert request_ref() is None


@pytest.mark.parametrize("block_type", ["ratelimited", "blocked"])
def test_blocked_response_cleans_up_if_start_response_fails(block_type):
    environ = create_environ("/")
    Request(environ)

    def start_response(status, headers):
        assert environ["werkzeug.request"] is not None
        raise RuntimeError("Response failed")

    result = {
        "block": True,
        "type": block_type,
        "trigger": "user",
        "retry_after_seconds": None,
    }
    with patch("aikido_zen.middleware.flask.should_block_request", return_value=result):
        with pytest.raises(RuntimeError, match="Response failed"):
            AikidoFlaskMiddleware(app=None)(environ, start_response)

    assert environ["werkzeug.request"] is None


@pytest.mark.parametrize(
    "decision", [{"block": False}, {"block": True, "type": "unknown"}]
)
def test_passthrough_preserves_request_for_streaming(decision):
    environ = create_environ("/")
    outer_request = Request(environ)

    def stream():
        assert environ["werkzeug.request"] is outer_request
        yield b"first"
        assert environ["werkzeug.request"] is outer_request
        yield b"second"

    body = stream()
    downstream = Mock(return_value=body)
    start_response = Mock()
    try:
        with patch(
            "aikido_zen.middleware.flask.should_block_request", return_value=decision
        ):
            result = AikidoFlaskMiddleware(downstream)(environ, start_response)
        assert result is body
        assert b"".join(result) == b"firstsecond"
        downstream.assert_called_once_with(environ, start_response)
    finally:
        body.close()
        environ["werkzeug.request"] = None
