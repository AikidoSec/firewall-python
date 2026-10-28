import pytest
from unittest.mock import MagicMock
from .packages import is_package_compatible, ANY_VERSION


@pytest.fixture
def mock_get_ipc(mocker):
    """Fixture to mock the get_ipc function."""

    class FakeComms:
        def __init__(self):
            self.action = None
            self.obj = None

        def send_message(self, message):
            self.action = message.identifier
            self.obj = message.request
            return {"success": True, "data": True}

    return FakeComms


def test_pkg_compat_check_success(mock_get_ipc, mocker):
    """Test successful wrapping of a package."""
    pkg_name = "example_package"
    pkg_version = "1.0.0"
    mock_class = mock_get_ipc()
    # Mock the metadata.version function
    mocker.patch("importlib.metadata.version", return_value=pkg_version)
    mocker.patch(
        "aikido_zen.background_process.ipc.IPCClient.get", return_value=mock_class
    )

    # Call the function under test
    is_package_compatible(pkg_name, ANY_VERSION)


def test_pkg_compat_check_retry(mock_get_ipc, mocker):
    """Test retry logic when sending data fails."""
    pkg_name = "example_package"
    pkg_version = "1.0.0"
    mock_class = mock_get_ipc()  # Create an instance of FakeComms

    # Mock the metadata.version function
    mocker.patch("importlib.metadata.version", return_value=pkg_version)
    # Mock the get_ipc function to return the mock_class instance
    mocker.patch(
        "aikido_zen.background_process.ipc.IPCClient.get", return_value=mock_class
    )

    mock_class.send_message = MagicMock(
        return_value={
            "success": False,
            "data": False,
        }
    )

    # Call the function under test
    is_package_compatible(pkg_name, ANY_VERSION)


def test_pkg_compat_check_partial_success(mock_get_ipc, mocker):
    """Test that the function stops retrying after a successful attempt."""
    pkg_name = "example_package"
    pkg_version = "1.0.0"
    mock_class = mock_get_ipc()  # Create an instance of FakeComms

    # Mock the metadata.version function
    mocker.patch("importlib.metadata.version", return_value=pkg_version)
    # Mock the get_ipc function to return the mock_class instance
    mocker.patch(
        "aikido_zen.background_process.ipc.IPCClient.get", return_value=mock_class
    )

    mock_class.send_message = MagicMock(
        side_effect=[
            {"success": False, "data": False},  # First attempt fails
            {"success": True, "data": True},  # Second attempt succeeds
        ]
    )

    # Call the function under test
    is_package_compatible(pkg_name, ANY_VERSION)
