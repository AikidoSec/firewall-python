import pytest
from aikido_zen.background_process.api.http_api import ReportingApiHTTP

# Sample event data for testing
sample_event = {"event_type": "test_event", "data": {"key": "value"}}


def test_report_data_401_code():
    api = ReportingApiHTTP("https://guard.aikido.dev/")

    response = api.report("wrong_token", sample_event, 5)

    assert response == {"success": False, "error": "invalid_token"}


def test_report_local_valid():
    api = ReportingApiHTTP("http://localhost:5000/")

    response = api.report("mocked_token", sample_event, 5)

    assert response == {
        "success": True,
        "blockedUserIds": [],
        "endpoints": [
            {
                "forceProtectionOff": False,
                "graphql": False,
                "method": "*",
                "rateLimiting": {
                    "enabled": True,
                    "maxRequests": 2,
                    "windowSizeInMS": 5000,
                },
                "route": "/test_ratelimiting_1",
            }
        ],
        "receivedAnyStats": False,
    }


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
