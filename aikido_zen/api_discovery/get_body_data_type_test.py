import pytest
from .get_body_data_type import get_body_data_type


def test_get_body_data_type():
    assert get_body_data_type({"CONTENT_TYPE": "application/json"}) == "json"
    assert get_body_data_type({"CONTENT_TYPE": "application/vnd.api+json"}) == "json"
    assert get_body_data_type({"CONTENT_TYPE": "application/csp-report"}) == "json"
    assert get_body_data_type({"CONTENT_TYPE": "application/x-json"}) == "json"
    assert (
        get_body_data_type({"CONTENT_TYPE": "application/x-www-form-urlencoded"})
        == "form-urlencoded"
    )
    assert get_body_data_type({"CONTENT_TYPE": "multipart/form-data"}) == "form-data"
    assert get_body_data_type({"CONTENT_TYPE": "text/xml"}) == "xml"
    assert get_body_data_type({"CONTENT_TYPE": "text/html"}) is None
    assert (
        get_body_data_type({"CONTENT_TYPE": ["application/json", "text/html"]})
        == "json"
    )
    assert get_body_data_type({"x-test": "abc"}) is None
    assert get_body_data_type(None) is None  # Testing invalid input
    assert get_body_data_type({}) is None
