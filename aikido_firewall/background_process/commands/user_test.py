import pytest
from unittest.mock import MagicMock
from .user import process_user


@pytest.fixture
def mock_reporter():
    """Fixture to create a mock reporter with a users attribute."""
    reporter = MagicMock()
    reporter.users = MagicMock()
    return reporter


@pytest.fixture
def mock_bg_process(mock_reporter):
    """Fixture to create a mock background process with a reporter."""
    bg_process = MagicMock()
    bg_process.reporter = mock_reporter
    return bg_process


def test_process_user_adds_user(mock_bg_process):
    """Test that process_user adds a user when reporter is present."""
    user_data = {"username": "test_user", "email": "test@example.com"}

    process_user(mock_bg_process, user_data, None)  # conn is not used in this function

    # Check that the add_user method was called with the correct arguments
    mock_bg_process.reporter.users.add_user.assert_called_once_with(user_data)


def test_process_user_no_reporter():
    """Test that process_user does nothing when reporter is not present."""
    bg_process = MagicMock()
    bg_process.reporter = None
    user_data = {"username": "test_user", "email": "test@example.com"}

    process_user(bg_process, user_data, None)  # conn is not used in this function

    # Make sure there were no errors
