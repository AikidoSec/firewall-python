import pytest
from .headers import Headers


def test_store_header_single_value():
    headers = Headers()
    headers.store_header("CONTENT_TYPE", "application/json")
    assert headers["CONTENT_TYPE"] == ["application/json"]


def test_store_header_multiple_values():
    headers = Headers()
    headers.store_headers("CONTENT_TYPE", ["application/json"])
    headers.store_headers("CONTENT_TYPE", ["text/html"])
    assert headers["CONTENT_TYPE"] == ["application/json", "text/html"]


def test_get_header_existing_key():
    headers = Headers()
    headers.store_header("CONTENT_TYPE", "application/json")
    assert headers.get_header("CONTENT_TYPE") == "application/json"


def test_get_header_non_existing_key():
    headers = Headers()
    assert headers.get_header("NON_EXISTING_KEY") is None


def test_get_header_multiple_values():
    headers = Headers()
    headers.store_headers("CONTENT_TYPE", ["application/json", "text/html"])
    assert headers.get_header("CONTENT_TYPE") == "text/html"


def test_validate_header_key_valid():
    try:
        Headers.validate_header_key("VALID_HEADER")
    except ValueError:
        pytest.fail("validate_header_key raised ValueError unexpectedly!")


def test_validate_header_key_not_uppercase():
    with pytest.raises(ValueError, match="Header key must be uppercase."):
        Headers.validate_header_key("invalid_header")


def test_validate_header_key_with_dash():
    with pytest.raises(
        ValueError, match="Header key must use underscores instead of dashes."
    ):
        Headers.validate_header_key("INVALID-HEADER")


def test_normalize_header_key_valid():
    assert Headers.normalize_header_key("valid-header") == "VALID_HEADER"
    assert Headers.normalize_header_key("ANOTHER-HEADER") == "ANOTHER_HEADER"


def test_normalize_header_key_already_normalized():
    assert Headers.normalize_header_key("ALREADY_NORMALIZED") == "ALREADY_NORMALIZED"


def test_store_headers_with_empty_list():
    headers = Headers()
    headers.store_headers("CONTENT_TYPE", [])
    assert headers.get_header("CONTENT_TYPE") is None


def test_store_header_with_empty_string():
    headers = Headers()
    headers.store_header("CONTENT_TYPE", "")
    assert headers.get_header("CONTENT_TYPE") == ""
