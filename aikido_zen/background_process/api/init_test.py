import pytest
from aikido_zen.background_process.api import ReportingApi

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
