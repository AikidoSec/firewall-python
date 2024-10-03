import pytest
from unittest.mock import MagicMock, patch
from .route import process_route


@pytest.fixture
def mock_connection_manager():
    """Fixture to create a mock connection_manager with a routes attribute."""
    connection_manager = MagicMock()
    connection_manager.routes = MagicMock()
    return connection_manager


def test_process_route_adds_route(mock_connection_manager):
    """Test that process_route adds a route when connection_manager is present."""
    data = {"route_metadata": 123456, "apispec": 2345}

    process_route(
        mock_connection_manager, data, None
    )  # conn is not used in this function

    # Check that the add_route method was called with the correct arguments
    mock_connection_manager.routes.add_route.assert_called_once_with(123456)
    mock_connection_manager.routes.update_route_with_apispec.assert_called_once_with(
        123456, 2345
    )


def test_process_route_no_connection_manager():
    """Test that process_route does nothing when connection_manager is not present."""
    data = {"route_metadata": 123456, "apispec": 2345}

    process_route(None, data, None)  # conn is not used in this function

    # Check that no error occurs
