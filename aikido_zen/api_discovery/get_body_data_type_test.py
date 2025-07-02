import pytest
from .get_body_data_type import get_body_data_type
from ..helpers.headers import Headers


def test_get_body_data_type():
    headers = Headers()
    headers.store_header("CONTENT_TYPE", "application/json")
    assert get_body_data_type(headers) == "json"

    headers = Headers()
    headers.store_header("CONTENT_TYPE", "application/vnd.api+json")
    assert get_body_data_type(headers) == "json"

    headers = Headers()
    headers.store_header("CONTENT_TYPE", "application/csp-report")
    assert get_body_data_type(headers) == "json"

    headers = Headers()
    headers.store_header("CONTENT_TYPE", "application/x-json")
    assert get_body_data_type(headers) == "json"

    headers = Headers()
    headers.store_header("CONTENT_TYPE", "application/x-www-form-urlencoded")
    assert get_body_data_type(headers) == "form-urlencoded"

    headers = Headers()
    headers.store_header("CONTENT_TYPE", "multipart/form-data")
    assert get_body_data_type(headers) == "form-data"

    headers = Headers()
    headers.store_header("CONTENT_TYPE", "text/xml")
    assert get_body_data_type(headers) == "xml"

    headers = Headers()
    headers.store_header("CONTENT_TYPE", "text/html")
    assert get_body_data_type(headers) is None

    headers = Headers()
    headers.store_header("CONTENT_TYPE", "application/json, text/html")
    assert get_body_data_type(headers) == "json"

    headers = Headers()
    headers.store_header("x-test", "abc")
    assert get_body_data_type(headers) is None

    headers = Headers()
    assert get_body_data_type(headers) is None  # Testing invalid input

    headers = Headers()
    assert get_body_data_type(headers) is None
