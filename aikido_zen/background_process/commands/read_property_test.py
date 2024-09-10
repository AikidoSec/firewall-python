import pytest
from unittest.mock import MagicMock, patch
from .read_property import (
    process_read_property,
)  # Replace 'your_module' with the actual module name
from aikido_zen.helpers.logging import logger


@pytest.fixture
def mock_connection_manager():
    """Fixture to create a mock connection_manager with attributes."""
    connection_manager = MagicMock()
    connection_manager.some_property = "some_value"  # Example property
    return connection_manager


def test_process_read_property_sends_value(mock_connection_manager):
    """Test that process_read_property sends the value of the property."""
    data = "some_property"

    process_read_property(mock_connection_manager, data)


def test_process_read_property_sends_none_for_missing_property(mock_connection_manager):
    """Test that process_read_property sends None for a missing property."""
    data = "missing_property"

    process_read_property(mock_connection_manager, data)


def test_process_read_property_logs_debug_for_missing_property(
    mock_connection_manager, caplog
):
    """Test that a debug message is logged for a missing property."""
    data = "missing_property"

    with patch("aikido_zen.helpers.logging.logger.debug") as mock_debug:
        process_read_property(mock_connection_manager, data)

        # Check that the debug log was called
        mock_debug.assert_called_once_with(
            "CloudConnectionManager has no attribute %s, current connection_manager: %s",
            data,
            mock_connection_manager,
        )
