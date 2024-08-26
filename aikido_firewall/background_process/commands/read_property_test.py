import pytest
from unittest.mock import MagicMock, patch
from .read_property import (
    process_read_property,
)  # Replace 'your_module' with the actual module name
from aikido_firewall.helpers.logging import logger


@pytest.fixture
def mock_reporter():
    """Fixture to create a mock reporter with attributes."""
    reporter = MagicMock()
    reporter.some_property = "some_value"  # Example property
    return reporter


@pytest.fixture
def mock_conn():
    """Fixture to create a mock connection."""
    conn = MagicMock()
    return conn


def test_process_read_property_sends_value(mock_reporter, mock_conn):
    """Test that process_read_property sends the value of the property."""
    data = "some_property"

    process_read_property(mock_reporter, data, mock_conn)

    # Check that the value was sent through the connection
    mock_conn.send.assert_called_once_with("some_value")


def test_process_read_property_sends_none_for_missing_property(
    mock_reporter, mock_conn
):
    """Test that process_read_property sends None for a missing property."""
    data = "missing_property"

    process_read_property(mock_reporter, data, mock_conn)

    # Check that None was sent through the connection
    mock_conn.send.assert_called_once_with(None)


def test_process_read_property_logs_debug_for_missing_property(
    mock_reporter, mock_conn, caplog
):
    """Test that a debug message is logged for a missing property."""
    data = "missing_property"

    with patch("aikido_firewall.helpers.logging.logger.debug") as mock_debug:
        process_read_property(mock_reporter, data, mock_conn)

        # Check that the debug log was called
        mock_debug.assert_called_once_with(
            "Reporter has no attribute %s, current reporter: %s",
            data,
            mock_reporter,
        )
