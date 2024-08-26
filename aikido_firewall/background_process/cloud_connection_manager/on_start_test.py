import pytest
from unittest.mock import MagicMock, patch
from .on_start import on_start


@pytest.fixture
def mock_connection_manager():
    connection_manager = MagicMock()
    connection_manager.token = "test_token"
    connection_manager.timeout_in_sec = 5
    connection_manager.api.report = MagicMock(return_value={"success": True})
    connection_manager.get_manager_info = lambda: {}
    connection_manager.update_service_config = MagicMock()
    return connection_manager


def test_on_start_no_token():
    """Test that no API call is made when the connection_manager has no token."""
    connection_manager = MagicMock()
    connection_manager.token = None
    on_start(connection_manager)
    connection_manager.api.report.assert_not_called()


def test_on_start_success(mock_connection_manager, caplog):
    """Test that the API call is made successfully and the service config is updated."""
    on_start(mock_connection_manager)

    # Check that the API report method was called
    mock_connection_manager.api.report.assert_called_once()

    # Check that the service config was updated
    mock_connection_manager.update_service_config.assert_called_once()

    # Check that the info log was called
    assert "Established connection with Aikido Server" in caplog.text


def test_on_start_failure(mock_connection_manager, caplog):
    """Test that an error is logged when the API call fails."""
    mock_connection_manager.api.report.return_value = {
        "success": False,
        "error": "Some error",
    }

    on_start(mock_connection_manager)

    # Check that the API report method was called
    mock_connection_manager.api.report.assert_called_once()

    # Check that the service config was not updated
    mock_connection_manager.update_service_config.assert_not_called()

    # Check that the error log was called
    assert "Failed to communicate with Aikido Server : Some error" in caplog.text
