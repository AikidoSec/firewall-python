from unittest.mock import patch

import pytest

from .asgi import AikidoASGIMiddleware


async def call_middleware(result):
    sent = []

    async def app(scope, receive, send):
        raise AssertionError("app should not be called")

    async def send(message):
        sent.append(message)

    with patch("aikido_zen.middleware.asgi.should_block_request", return_value=result):
        await AikidoASGIMiddleware(app)({"type": "http"}, None, send)
    return sent


@pytest.mark.asyncio
async def test_rate_limited_response_has_retry_after():
    sent = await call_middleware(
        {
            "block": True,
            "type": "ratelimited",
            "trigger": "user",
            "ip": "1.1.1.1",
            "retry_after_seconds": 7,
        }
    )
    assert sent[0]["status"] == 429
    assert sent[0]["headers"] == [
        (b"content-type", b"text/plain"),
        (b"retry-after", b"7"),
    ]
    assert sent[1]["body"] == b"You are rate limited by Zen."


@pytest.mark.asyncio
async def test_rate_limited_response_without_retry_after_seconds():
    sent = await call_middleware(
        {
            "block": True,
            "type": "ratelimited",
            "trigger": "user",
            "ip": "1.1.1.1",
            "retry_after_seconds": None,
        }
    )
    assert sent[0]["status"] == 429
    assert sent[0]["headers"] == [(b"content-type", b"text/plain")]


@pytest.mark.asyncio
async def test_blocked_user_response_has_no_retry_after():
    sent = await call_middleware({"block": True, "type": "blocked", "trigger": "user"})
    assert sent[0]["status"] == 403
    assert sent[0]["headers"] == [(b"content-type", b"text/plain")]
