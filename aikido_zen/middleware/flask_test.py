from unittest.mock import patch

from werkzeug.test import create_environ

from .flask import AikidoFlaskMiddleware


def call_middleware(result):
    captured = {}

    def start_response(status, headers, exc_info=None):
        captured["status"] = status
        captured["headers"] = dict(headers)

    with patch("aikido_zen.middleware.flask.should_block_request", return_value=result):
        middleware = AikidoFlaskMiddleware(app=None)
        captured["body"] = b"".join(middleware(create_environ("/"), start_response))
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
