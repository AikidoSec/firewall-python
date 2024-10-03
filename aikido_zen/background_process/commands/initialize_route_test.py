import pytest
from unittest.mock import MagicMock, patch
from .initialize_route import process_initialize_route


@pytest.fixture
def mock_connection_manager():
    """Fixture to create a mock connection_manager with a routes attribute."""
    connection_manager = MagicMock()
    connection_manager.routes = MagicMock()
    return connection_manager


def test_process_initialize_route(mock_connection_manager):
    """Test that process_initialize_route adds a route when connection_manager is present."""
    data = 123456

    process_initialize_route(
        mock_connection_manager, data, None
    )  # conn is not used in this function

    # Check that increment_route and initialize_route methods were called with the correct arguments
    mock_connection_manager.routes.initialize_route.assert_called_once_with(
        route_metadata=123456
    )
    mock_connection_manager.routes.increment_route.assert_called_once_with(
        route_metadata=123456
    )


def test_process_initialize_route_no_connection_manager():
    """Test that process_initialize_route does nothing when connection_manager is not present."""
    data = 123456

    process_initialize_route(None, data, None)  # conn is not used in this function

    # Check that no error occurs
