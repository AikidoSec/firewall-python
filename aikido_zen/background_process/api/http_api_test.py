import pytest
import requests
from unittest.mock import patch
from aikido_zen.background_process.api.http_api import (
    ReportingApiHTTP,
)  # Replace with the actual module name

# Sample event data for testing
sample_event = {"event_type": "test_event", "data": {"key": "value"}}


def test_report_data_401_code(monkeypatch):
    # Create an instance of ReportingApiHTTP
    api = ReportingApiHTTP("http://mocked-url.com/")

    # Mock the requests.post method to return a successful response
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    def mock_post(url, json, timeout, headers):
        return MockResponse({"success": False}, 401)

    monkeypatch.setattr(requests, "post", mock_post)

    # Call the report method
    response = api.report("mocked_token", sample_event, 5)

    # Assert the response
    assert response == {"success": False, "error": "invalid_token"}


def test_report_connection_error(monkeypatch):
    # Create an instance of ReportingApiHTTP
    api = ReportingApiHTTP("http://mocked-url.com/")

    # Mock the requests.post method to raise a ConnectionError
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            requests.exceptions.ConnectionError
        ),
    )

    # Call the report method
    response = api.report("mocked_token", sample_event, 5)

    # Assert the response
    assert response == {"success": False, "error": "timeout"}


def test_report_other_exception(monkeypatch):
    # Create an instance of ReportingApiHTTP
    api = ReportingApiHTTP("http://mocked-url.com/")

    # Mock the requests.post method to raise a generic exception
    def mock_post(url, json, timeout, headers):
        raise Exception("Some error occurred")

    monkeypatch.setattr(requests, "post", mock_post)

    # Call the report method
    response = api.report("mocked_token", sample_event, 5)

    # Assert that the response is None (or however you want to handle it)
    assert response["error"] is "unknown"
    assert not response["success"]
