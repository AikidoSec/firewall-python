from unittest.mock import patch

from .django import AikidoDjangoMiddleware


class FakeHttpResponse(dict):
    def __init__(self, content, content_type=None, status=200):
        super().__init__()
        self.content = content
        self.content_type = content_type
        self.status_code = status


def call_middleware(result):
    middleware = AikidoDjangoMiddleware(get_response=None)
    middleware.HttpResponse = FakeHttpResponse
    with patch(
        "aikido_zen.middleware.django.should_block_request", return_value=result
    ):
        return middleware(request=None)


def test_rate_limited_response_has_retry_after():
    response = call_middleware(
        {
            "block": True,
            "type": "ratelimited",
            "trigger": "user",
            "ip": "1.1.1.1",
            "retry_after_seconds": 7,
        }
    )
    assert response.status_code == 429
    assert response["Retry-After"] == "7"
    assert response.content == "You are rate limited by Zen."


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
    assert response.status_code == 429
    assert "Retry-After" not in response
