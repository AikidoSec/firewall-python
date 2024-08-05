import pytest
from pathlib import Path
from .parse_as_file_url import (
    parse_as_file_url,
)  # Replace 'your_module' with the actual module name


def test_valid_file_urls():
    assert parse_as_file_url("file:///home/user/test.txt") == str(
        Path("/home/user/test.txt").resolve()
    )
    assert parse_as_file_url("file:///etc/passwd") == str(Path("/etc/passwd").resolve())
    assert parse_as_file_url("file:///usr/local/bin/script.sh") == str(
        Path("/usr/local/bin/script.sh").resolve()
    )


def test_relative_paths():
    assert parse_as_file_url("test.txt") == "/test.txt"
    assert parse_as_file_url("./test.txt") == "/test.txt"
    assert parse_as_file_url("../test.txt") == "/test.txt"
    assert parse_as_file_url("folder/test.txt") == "/folder/test.txt"
    assert parse_as_file_url("folder/../test.txt") == "/test.txt"


def test_edge_cases():
    assert parse_as_file_url("") == "/"
    assert parse_as_file_url(".") == "/"
    assert parse_as_file_url("..") == "/"
    assert parse_as_file_url("/..") == "/"


def test_invalid_file_urls():
    assert parse_as_file_url("file:///invalid/path") == str(
        Path("/invalid/path").resolve()
    )
    assert parse_as_file_url("file:///../invalid/path") == str(
        Path("/invalid/path").resolve()
    )


def test_windows_paths():
    assert (
        parse_as_file_url("file:///C:/Users/User/test.txt") == "/C:/Users/User/test.txt"
    )
    assert (
        parse_as_file_url("file:///C:/Users/User/../test.txt") == "/C:/Users/test.txt"
    )
