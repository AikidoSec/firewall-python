import pytest
from aikido_zen.helpers.get_ua_from_context import get_ua_from_context


class Context:
    def __init__(self, headers):
        self.headers = headers


def test_user_agent_present():
    context = Context(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
    )
    assert (
        get_ua_from_context(context)
        == "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    )


def test_user_agent_present_case_insensitive():
    context = Context(
        {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
    )
    assert (
        get_ua_from_context(context)
        == "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    )


def test_user_agent_not_present():
    context = Context({"Accept": "text/html", "Content-Type": "application/json"})
    assert get_ua_from_context(context) is None


def test_user_agent_empty_value():
    context = Context({"User-Agent": ""})
    assert get_ua_from_context(context) == ""


def test_user_agent_with_other_headers():
    context = Context(
        {
            "Accept": "text/html",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; Pixel 3 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Mobile Safari/537.36",
        }
    )
    assert (
        get_ua_from_context(context)
        == "Mozilla/5.0 (Linux; Android 10; Pixel 3 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Mobile Safari/537.36"
    )
