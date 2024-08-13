import pytest
from .parse_cookies import parse_cookies


def test_parse_cookies_single_cookie():
    cookie_str = "sessionid=abc123"
    expected = {"sessionid": "abc123"}
    assert parse_cookies(cookie_str) == expected


def test_parse_cookies_multiple_cookies():
    cookie_str = "sessionid=abc123; user=JohnDoe; theme=dark"
    expected = {"sessionid": "abc123", "user": "JohnDoe", "theme": "dark"}
    assert parse_cookies(cookie_str) == expected


def test_parse_cookies_empty_string():
    cookie_str = ""
    expected = {}
    assert parse_cookies(cookie_str) == expected


def test_parse_cookies_with_special_characters():
    cookie_str = "sessionid=abc123; user=John@Doe; theme=dark&light"
    expected = {"sessionid": "abc123", "user": "John@Doe", "theme": "dark&light"}
    assert parse_cookies(cookie_str) == expected
