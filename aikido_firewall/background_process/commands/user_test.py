import pytest
from unittest.mock import MagicMock
from .user import process_user


@pytest.fixture
def mock_connection_manager():
    """Fixture to create a mock connection_manager with a users attribute."""
    connection_manager = MagicMock()
    connection_manager.users = MagicMock()
    return connection_manager


def test_process_user_adds_user(mock_connection_manager):
    """Test that process_user adds a user when connection_manager is present."""
    user_data = {"username": "test_user", "email": "test@example.com"}

    process_user(
        mock_connection_manager, user_data
    )  # conn is not used in this function

    # Check that the add_user method was called with the correct arguments
    mock_connection_manager.users.add_user.assert_called_once_with(user_data)


def test_process_user_no_connection_manager():
    """Test that process_user does nothing when connection_manager is not present."""
    user_data = {"username": "test_user", "email": "test@example.com"}

    process_user(None, user_data)  # conn is not used in this function
