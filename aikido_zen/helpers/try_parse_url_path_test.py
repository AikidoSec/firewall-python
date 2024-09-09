import pytest
from aikido_zen.helpers.try_parse_url_path import try_parse_url_path


def test_try_parse_url_path_nothing_found():
    assert try_parse_url_path("abc") is None


def test_try_parse_url_path_for_root():
    assert try_parse_url_path("/") == "/"


def test_try_parse_url_path_for_relative_url():
    assert try_parse_url_path("/posts") == "/posts"


def test_try_parse_url_path_for_relative_url_with_query():
    assert try_parse_url_path("/posts?abc=def") == "/posts"


def test_try_parse_url_path_for_absolute_url():
    assert try_parse_url_path("http://localhost/posts/3") == "/posts/3"


def test_try_parse_url_path_for_absolute_url_with_query():
    assert try_parse_url_path("http://localhost/posts/3?abc=def") == "/posts/3"


def test_try_parse_url_path_for_absolute_url_with_hash():
    assert try_parse_url_path("http://localhost/posts/3#abc") == "/posts/3"


def test_try_parse_url_path_for_absolute_url_with_query_and_hash():
    assert try_parse_url_path("http://localhost/posts/3?abc=def#ghi") == "/posts/3"


def test_try_parse_url_path_for_absolute_url_with_query_and_hash_no_path():
    assert try_parse_url_path("http://localhost/?abc=def#ghi") == "/"


def test_try_parse_url_path_for_absolute_url_with_query_no_path():
    assert try_parse_url_path("http://localhost?abc=def") == "/"


def test_try_parse_url_path_for_absolute_url_with_hash_no_path():
    assert try_parse_url_path("http://localhost#abc") == "/"
