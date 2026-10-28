import pytest
from unittest.mock import MagicMock
from .packages import is_package_compatible, is_version_supported, ANY_VERSION


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


@pytest.mark.parametrize(
    "version, required_version, expected",
    [
        ("2.8.6", "2.8.6", True),
        ("2.8.7", "2.8.6", True),
        ("2.10.0", "2.8.6", True),
        ("3.0", "2.8.6", True),
        ("2.8.5", "2.8.6", False),
        ("2.8", "2.8.6", False),
        ("1.0", "1.0.0", True),
        ("1.0.0.0", "1.0", True),
        ("0.9.0", "0.0.0", True),
        ("2.8.6rc1", "2.8.6", False),
        ("2.8.6a1", "2.8.6", False),
        ("2.8.6.dev0", "2.8.6", False),
        ("2.8.6rc1.post1", "2.8.6", False),
        ("2.8.6.post1", "2.8.6", True),
        ("2.8.6.post1.dev0", "2.8.6", True),
        ("2.8.6-1", "2.8.6", True),
        ("2.8.6+ubuntu-1", "2.8.6", True),
        ("2.8.7rc1", "2.8.6", True),
        ("v2.8.6", "2.8.6", True),
        (" 2.8.6 ", "2.8.6", True),
        ("1!0.1", "2.8.6", True),
    ],
)
def test_is_version_supported(version, required_version, expected):
    assert is_version_supported(version, required_version) is expected


@pytest.mark.parametrize(
    "version", ["2.8.6-foo", "garbage", "", "2.8.6+", "\u0663.\u0661"]
)
def test_is_version_supported_invalid_version(version):
    with pytest.raises(ValueError):
        is_version_supported(version, "2.8.6")


def test_pkg_compat_check_invalid_version(mocker):
    mocker.patch("importlib.metadata.version", return_value="2.2.4-foo")
    assert is_package_compatible("example_invalid_package", "2.2.4") is False


def test_packages_module_works_without_packaging(monkeypatch):
    import importlib.util
    import sys

    monkeypatch.setitem(sys.modules, "packaging", None)
    monkeypatch.setitem(sys.modules, "packaging.version", None)
    spec = importlib.util.find_spec("aikido_zen.background_process.packages")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.is_version_supported("3.1.0", "2.2.4") is True
