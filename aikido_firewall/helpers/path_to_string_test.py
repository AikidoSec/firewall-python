import pytest
from .path_to_string import path_to_string


def test_path_to_string_with_string():
    assert path_to_string("test.txt") == "test.txt"
    assert path_to_string("/home/user/file.txt") == "/home/user/file.txt"


def test_path_to_string_with_valid_url():
    assert path_to_string("file:///path/to/resource") == "/path/to/resource"
    assert path_to_string("file:///another/path") == "/another/path"


def test_path_to_string_with_bytes():
    assert path_to_string(b"test.txt") == "test.txt"
    assert path_to_string(b"/home/user/file.txt") == "/home/user/file.txt"
    assert path_to_string(b"\xff") is None  # Invalid UTF-8 byte sequence


def test_path_to_string_with_empty_string():
    assert path_to_string("") == ""


def test_path_to_string_with_none():
    assert path_to_string(None) is None


def test_path_to_string_with_other_types():
    assert path_to_string(123) is None  # Integer input
    assert path_to_string([]) is None  # List input
    assert path_to_string({}) is None  # Dictionary input
