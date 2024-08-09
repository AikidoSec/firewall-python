import pytest
from unittest.mock import MagicMock, patch
from .on_start import on_start


@pytest.fixture
def mock_reporter():
    reporter = MagicMock()
    reporter.token = "test_token"
    reporter.timeout_in_sec = 5
    reporter.api.report = MagicMock(return_value={"success": True})
    reporter.get_reporter_info = lambda: {}
    reporter.update_service_config = MagicMock()
    return reporter


def test_on_start_no_token():
    """Test that no API call is made when the reporter has no token."""
    reporter = MagicMock()
    reporter.token = None
    on_start(reporter)
    reporter.api.report.assert_not_called()


def test_on_start_success(mock_reporter, caplog):
    """Test that the API call is made successfully and the service config is updated."""
    on_start(mock_reporter)

    # Check that the API report method was called
    mock_reporter.api.report.assert_called_once()

    # Check that the service config was updated
    mock_reporter.update_service_config.assert_called_once()

    # Check that the info log was called
    assert "Established connection with Aikido Server" in caplog.text


def test_on_start_failure(mock_reporter, caplog):
    """Test that an error is logged when the API call fails."""
    mock_reporter.api.report.return_value = {"success": False, "error": "Some error"}

    on_start(mock_reporter)

    # Check that the API report method was called
    mock_reporter.api.report.assert_called_once()

    # Check that the service config was not updated
    mock_reporter.update_service_config.assert_not_called()

    # Check that the error log was called
    assert "Failed to communicate with Aikido Server : Some error" in caplog.text
