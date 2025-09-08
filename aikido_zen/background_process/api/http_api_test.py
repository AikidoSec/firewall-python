import requests
from aikido_zen.background_process.api.http_api import ReportingApiHTTP
from aikido_zen.background_process.api.helpers import ResponseError

# Sample event data for testing
sample_event = {"event_type": "test_event", "data": {"key": "value"}}


def test_report_data_401_code():
    # Create an instance of ReportingApiHTTP
    api = ReportingApiHTTP("https://guard.aikido.dev/")

    # Call the report method with an invalid token, see the 401
    response = api.report("mocked_token", sample_event, 5)

    # Assert the response
    assert response.success is False
    assert response.error is ResponseError.INVALID_TOKEN


def test_report_connection_error():
    # Create an instance of ReportingApiHTTP
    api = ReportingApiHTTP("http://localhost:5000/timeout5/")

    # Call the report method
    response = api.report("mocked_token", sample_event, 5)

    # Assert the response
    assert response.success == False
    assert response.error == ResponseError.TIMEOUT_ERROR


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
