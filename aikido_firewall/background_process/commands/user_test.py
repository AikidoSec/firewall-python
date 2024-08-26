import pytest
from unittest.mock import MagicMock
from .user import process_user


@pytest.fixture
def mock_reporter():
    """Fixture to create a mock reporter with a users attribute."""
    reporter = MagicMock()
    reporter.users = MagicMock()
    return reporter


def test_process_user_adds_user(mock_reporter):
    """Test that process_user adds a user when reporter is present."""
    user_data = {"username": "test_user", "email": "test@example.com"}

    process_user(mock_reporter, user_data, None)  # conn is not used in this function

    # Check that the add_user method was called with the correct arguments
    mock_reporter.users.add_user.assert_called_once_with(user_data)


def test_process_user_no_reporter():
    """Test that process_user does nothing when reporter is not present."""
    user_data = {"username": "test_user", "email": "test@example.com"}

    process_user(None, user_data, None)  # conn is not used in this function

    # Make sure there were no errors
