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


@pytest.mark.parametrize(
    "cookie_str, expected",
    [
        (
            'user={"username":{"$regex":".*"}}; ,2=2',
            {"user": '{"username":{"$regex":".*"}}', ",2": "2"},
        ),
        ('user={"a":1}', {"user": '{"a":1}'}),
        ("id=1' OR '1'='1", {"id": "1' OR '1'='1"}),
        (",2=2; id=abc", {",2": "2", "id": "abc"}),
        ('user={"a":1}; sid=abc', {"user": '{"a":1}', "sid": "abc"}),
        (
            'sid=abc; user={"a":1}; theme=dark',
            {"sid": "abc", "user": '{"a":1}', "theme": "dark"},
        ),
        ("novalue", {"": "novalue"}),
    ],
)
def test_parse_cookies_keeps_cookies_simplecookie_rejects(cookie_str, expected):
    assert parse_cookies(cookie_str) == expected


@pytest.mark.parametrize(
    "cookie_strs, expected",
    [
        (["id=a; id=b"], {"id": ["a", "b"]}),
        (["id=a", "id=b"], {"id": ["a", "b"]}),
        (["id=a; sid=1", "id=a"], {"id": "a", "sid": "1"}),
        (['id="a b"'], {"id": "a b"}),
        (['id="a\\"b"'], {"id": 'a"b'}),
        (["name=café"], {"name": "café"}),
        (["café=1"], {"café": "1"}),
    ],
)
def test_parse_cookies_keeps_every_value(cookie_strs, expected):
    assert parse_cookies(*cookie_strs) == expected
