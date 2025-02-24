import pytest
from unittest.mock import MagicMock
from .packages import pkg_compat_check, ANY_VERSION


@pytest.fixture
def mock_get_comms(mocker):
    """Fixture to mock the get_comms function."""

    class FakeComms:
        def __init__(self):
            self.action = None
            self.obj = None
            self.receive = False

        def send_data_to_bg_process(self, action, obj, receive):
            self.action = action
            self.obj = obj
            self.receive = receive
            return {"success": True, "data": True}

    return FakeComms


def test_pkg_compat_check_success(mock_get_comms, mocker):
    """Test successful wrapping of a package."""
    pkg_name = "example_package"
    pkg_version = "1.0.0"
    mock_class = mock_get_comms()
    # Mock the metadata.version function
    mocker.patch("importlib.metadata.version", return_value=pkg_version)
    mocker.patch(
        "aikido_zen.background_process.comms.get_comms", return_value=mock_class
    )

    # Call the function under test
    pkg_compat_check(pkg_name, ANY_VERSION)


def test_pkg_compat_check_retry(mock_get_comms, mocker):
    """Test retry logic when sending data fails."""
    pkg_name = "example_package"
    pkg_version = "1.0.0"
    mock_class = mock_get_comms()  # Create an instance of FakeComms

    # Mock the metadata.version function
    mocker.patch("importlib.metadata.version", return_value=pkg_version)
    # Mock the get_comms function to return the mock_class instance
    mocker.patch(
        "aikido_zen.background_process.comms.get_comms", return_value=mock_class
    )

    # Mock the send_data_to_bg_process method to simulate failure
    mock_class.send_data_to_bg_process = MagicMock(
        return_value={
            "success": False,
            "data": False,
        }
    )

    # Call the function under test
    pkg_compat_check(pkg_name, ANY_VERSION)


def test_pkg_compat_check_partial_success(mock_get_comms, mocker):
    """Test that the function stops retrying after a successful attempt."""
    pkg_name = "example_package"
    pkg_version = "1.0.0"
    mock_class = mock_get_comms()  # Create an instance of FakeComms

    # Mock the metadata.version function
    mocker.patch("importlib.metadata.version", return_value=pkg_version)
    # Mock the get_comms function to return the mock_class instance
    mocker.patch(
        "aikido_zen.background_process.comms.get_comms", return_value=mock_class
    )

    # Mock the send_data_to_bg_process method to simulate a failure followed by success
    mock_class.send_data_to_bg_process = MagicMock(
        side_effect=[
            {"success": False, "data": False},  # First attempt fails
            {"success": True, "data": True},  # Second attempt succeeds
        ]
    )

    # Call the function under test
    pkg_compat_check(pkg_name, ANY_VERSION)
