import pytest
from aikido_firewall.agent.api import Token, ReportingApi

# Test ReportingApi Class :
from requests.models import Response


@pytest.fixture
def reporting_api():
    return ReportingApi()


def test_to_api_response_rate_limited(reporting_api):
    res = Response()
    res.status_code = 429
    assert reporting_api.to_api_response(res) == {
        "success": False,
        "error": "rate_limited",
    }


def test_to_api_response_invalid_token(reporting_api):
    res = Response()
    res.status_code = 401
    assert reporting_api.to_api_response(res) == {
        "success": False,
        "error": "invalid_token",
    }


def test_to_api_response_unknown_error(reporting_api):
    res = Response()
    res.status_code = 500  # Simulating an unknown error status code
    assert reporting_api.to_api_response(res) == {
        "success": False,
        "error": "unknown_error",
    }


def test_to_api_response_valid_json(reporting_api):
    res = Response()
    res.status_code = 200
    res._content = b'{"key": "value"}'  # Simulating valid JSON response
    assert reporting_api.to_api_response(res) == {"key": "value"}


# Test Token Class :
def test_token_valid_string():
    token_str = "my_token"
    token = Token(token_str)
    assert str(token) == token_str


def test_token_empty_string():
    with pytest.raises(ValueError):
        Token("")


def test_token_invalid_type():
    with pytest.raises(ValueError):
        Token(123)


def test_token_instance():
    token_str = "my_token"
    token = Token(token_str)
    assert isinstance(token, Token)
