import pytest
from unittest.mock import MagicMock, patch
from . import read_property
from aikido_zen.helpers.logging import logger


@pytest.fixture
def mock_connection_manager():
    """Fixture to create a mock connection_manager with attributes."""
    connection_manager = MagicMock()
    connection_manager.some_property = "some_value"  # Example property
    return connection_manager


def test_process_read_property_sends_value(mock_connection_manager):
    data = "some_property"

    read_property.process(mock_connection_manager, data, None)


def test_process_read_property_sends_none_for_missing_property(mock_connection_manager):
    data = "missing_property"

    read_property.process(mock_connection_manager, data, None)


def test_process_read_property_logs_debug_for_missing_property(
    mock_connection_manager, caplog
):
    """Test that a debug message is logged for a missing property."""
    data = "missing_property"

    with patch("aikido_zen.helpers.logging.logger.debug") as mock_debug:
        read_property.process(mock_connection_manager, data, None)

        # Check that the debug log was called
        mock_debug.assert_called_once_with(
            "CloudConnectionManager has no attribute %s, current connection_manager: %s",
            data,
            mock_connection_manager,
        )
