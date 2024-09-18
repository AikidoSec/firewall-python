import pytest
from .get_auth_types import get_auth_types


class Context:
    def __init__(self, headers={}, cookies={}):
        self.headers = headers
        self.cookies = cookies


def test_detects_authorization_header():
    context1 = Context(headers={"AUTHORIZATION": "Bearer token"})
    assert get_auth_types(context1) == [{"type": "http", "scheme": "bearer"}]

    context2 = Context(headers={"AUTHORIZATION": "Basic base64"})
    assert get_auth_types(context2) == [{"type": "http", "scheme": "basic"}]

    context3 = Context(headers={"AUTHORIZATION": "custom"})
    assert get_auth_types(context3) == [
        {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
        }
    ]


def test_detects_api_keys():
    context1 = Context(headers={"X_API_KEY": "token"})
    assert get_auth_types(context1) == [
        {"type": "apiKey", "in": "header", "name": "x-api-key"}
    ]

    context2 = Context(headers={"API_KEY": "token"})
    assert get_auth_types(context2) == [
        {"type": "apiKey", "in": "header", "name": "api-key"}
    ]


def test_detects_auth_cookies():
    context1 = Context(cookies={"api-key": "token"})
    assert get_auth_types(context1) == [
        {"type": "apiKey", "in": "cookie", "name": "api-key"}
    ]

    context2 = Context(cookies={"session": "test"})
    assert get_auth_types(context2) == [
        {
            "type": "apiKey",
            "in": "cookie",
            "name": "session",
        }
    ]


def test_no_auth():
    assert get_auth_types(Context()) is None
    assert get_auth_types(Context(headers={})) is None
    assert get_auth_types(Context(headers={"AUTHORIZATION": ""})) is None
    assert get_auth_types(Context(headers={"AUTHORIZATION": None})) is None
