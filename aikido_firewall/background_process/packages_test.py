import pytest
from unittest.mock import MagicMock
from .packages import add_wrapped_package


@pytest.fixture
def mock_get_comms(mocker):
    """Fixture to mock the get_comms function."""

    class FakeComms:
        def __init__(self):
            self.action = None
            self.obj = None
            self.receive = False

        def dispatch_command(self, action, obj, receive):
            self.action = action
            self.obj = obj
            self.receive = receive
            return {"success": True, "data": True}

    return FakeComms


def test_add_wrapped_package_success(mock_get_comms, mocker):
    """Test successful wrapping of a package."""
    pkg_name = "example_package"
    pkg_version = "1.0.0"
    mock_class = mock_get_comms()
    # Mock the metadata.version function
    mocker.patch("importlib.metadata.version", return_value=pkg_version)
    mocker.patch(
        "aikido_firewall.background_process.comms.get_comms", return_value=mock_class
    )

    # Call the function under test
    add_wrapped_package(pkg_name)

    # Assert that the version was retrieved and the dispatch_command was called
    assert mock_class.action == "WRAPPED_PACKAGE"
    assert mock_class.obj == {
        "name": pkg_name,
        "details": {
            "version": pkg_version,
            "supported": True,
        },
    }
    assert mock_class.receive == True


def test_add_wrapped_package_retry(mock_get_comms, mocker):
    """Test retry logic when sending data fails."""
    pkg_name = "example_package"
    pkg_version = "1.0.0"
    mock_class = mock_get_comms()  # Create an instance of FakeComms

    # Mock the metadata.version function
    mocker.patch("importlib.metadata.version", return_value=pkg_version)
    # Mock the get_comms function to return the mock_class instance
    mocker.patch(
        "aikido_firewall.background_process.comms.get_comms", return_value=mock_class
    )

    # Mock the dispatch_command method to simulate failure
    mock_class.dispatch_command = MagicMock(
        return_value={
            "success": False,
            "data": False,
        }
    )

    # Call the function under test
    add_wrapped_package(pkg_name)

    # Assert that dispatch_command was called MAX_REPORT_TRIES times
    assert mock_class.dispatch_command.call_count == 5


def test_add_wrapped_package_partial_success(mock_get_comms, mocker):
    """Test that the function stops retrying after a successful attempt."""
    pkg_name = "example_package"
    pkg_version = "1.0.0"
    mock_class = mock_get_comms()  # Create an instance of FakeComms

    # Mock the metadata.version function
    mocker.patch("importlib.metadata.version", return_value=pkg_version)
    # Mock the get_comms function to return the mock_class instance
    mocker.patch(
        "aikido_firewall.background_process.comms.get_comms", return_value=mock_class
    )

    # Mock the dispatch_command method to simulate a failure followed by success
    mock_class.dispatch_command = MagicMock(
        side_effect=[
            {"success": False, "data": False},  # First attempt fails
            {"success": True, "data": True},  # Second attempt succeeds
        ]
    )

    # Call the function under test
    add_wrapped_package(pkg_name)

    # Assert that dispatch_command was called twice
    assert mock_class.dispatch_command.call_count == 2
