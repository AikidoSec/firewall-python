import pytest
import socket
from unittest.mock import MagicMock, patch
from .get_manager_info import get_manager_info


# Sample connection_manager object for testing
class MockCloudConnectionManager:
    def __init__(self, block, packages, serverless):
        self.block = block
        self.packages = packages
        self.serverless = serverless


@pytest.fixture
def mock_connection_manager():
    return MockCloudConnectionManager(
        block=True,
        packages={
            "package1": {"version": "1.0.0", "supported": True},
            "package2": {"version": "2.0.0", "supported": False},
            "package3": {"version": "3.0.0", "supported": True},
        },
        serverless=True,
    )


# Fixture to patch socket.gethostname
@pytest.fixture(autouse=True)
def patch_gethostname(monkeypatch):
    monkeypatch.setattr(socket, "gethostname", lambda: "test-hostname")


@patch("platform.system", return_value="Linux")
@patch("platform.release", return_value="5.4.0")
@patch("aikido_zen.helpers.get_machine_ip.get_ip", return_value="192.168.1.1")
@patch("aikido_zen.config.PKG_VERSION", "PKG_VERSION")
def test_get_manager_info(
    mock_get_ip,
    mock_platform_release,
    mock_platform_system,
    mock_connection_manager,
    monkeypatch,
):
    connection_manager_info = get_manager_info(mock_connection_manager)
    print(connection_manager_info)
    assert connection_manager_info["dryMode"] is False
    assert connection_manager_info["hostname"] == "test-hostname"
    assert (
        connection_manager_info["version"] == "PKG_VERSION"
    )  # Replace with actual version if needed
    assert connection_manager_info["library"] == "firewall-python"
    assert connection_manager_info["ipAddress"] == "192.168.1.1"
    assert connection_manager_info["packages"] == {
        "package1": "1.0.0",
        "package3": "3.0.0",
    }
    assert connection_manager_info["serverless"] is True
    assert connection_manager_info["stack"] == [
        "package1",
        "package2",
        "package3",
        True,
    ]
    assert connection_manager_info["os"] == {"name": "Linux", "version": "5.4.0"}
    assert connection_manager_info["preventedPrototypePollution"] is False
    assert connection_manager_info["nodeEnv"] == ""


def test_get_manager_info_with_empty_packages():
    mock_connection_manager = MockCloudConnectionManager(
        block=False, packages={}, serverless=False
    )
    with patch("platform.system", return_value="Linux"), patch(
        "platform.release", return_value="5.4.0"
    ), patch("aikido_zen.helpers.get_machine_ip.get_ip", return_value="192.168.1.1"):
        connection_manager_info = get_manager_info(mock_connection_manager)

        assert connection_manager_info["packages"] == {}
        assert connection_manager_info["stack"] == []


def test_get_manager_info_with_unsupported_packages():
    mock_connection_manager = MockCloudConnectionManager(
        block=False,
        packages={
            "package1": {"version": "1.0.0", "supported": True},
            "package2": {"version": "2.0.0", "supported": False},
        },
        serverless=False,
    )

    with patch("platform.system", return_value="Linux"), patch(
        "platform.release", return_value="5.4.0"
    ), patch("aikido_zen.helpers.get_machine_ip.get_ip", return_value="192.168.1.1"):
        connection_manager_info = get_manager_info(mock_connection_manager)

        assert connection_manager_info["packages"] == {"package1": "1.0.0"}
        assert connection_manager_info["stack"] == ["package1", "package2"]


def test_get_manager_info_with_non_serverless():
    mock_connection_manager = MockCloudConnectionManager(
        block=False,
        packages={"package1": {"version": "1.0.0", "supported": True}},
        serverless=False,
    )

    with patch("platform.system", return_value="Linux"), patch(
        "platform.release", return_value="5.4.0"
    ), patch("aikido_zen.helpers.get_machine_ip.get_ip", return_value="192.168.1.1"):
        connection_manager_info = get_manager_info(mock_connection_manager)

        assert connection_manager_info["serverless"] is False
        assert connection_manager_info["stack"] == ["package1"]


def test_get_manager_info_with_blocked_connection_manager():
    mock_connection_manager = MockCloudConnectionManager(
        block=True,
        packages={"package1": {"version": "1.0.0", "supported": True}},
        serverless=False,
    )

    with patch("platform.system", return_value="Linux"), patch(
        "platform.release", return_value="5.4.0"
    ), patch("aikido_zen.helpers.get_machine_ip.get_ip", return_value="192.168.1.1"):
        connection_manager_info = get_manager_info(mock_connection_manager)

        assert connection_manager_info["dryMode"] is False


def test_get_manager_info_with_drymode_connection_manager():
    mock_connection_manager = MockCloudConnectionManager(
        block=False,
        packages={"package1": {"version": "1.0.0", "supported": True}},
        serverless=False,
    )

    with patch("platform.system", return_value="Linux"), patch(
        "platform.release", return_value="5.4.0"
    ), patch("aikido_zen.helpers.get_machine_ip.get_ip", return_value="192.168.1.1"):
        connection_manager_info = get_manager_info(mock_connection_manager)

        assert connection_manager_info["dryMode"] is True


def test_get_manager_info_with_different_os():
    mock_connection_manager = MockCloudConnectionManager(
        block=False,
        packages={"package1": {"version": "1.0.0", "supported": True}},
        serverless=False,
    )

    with patch("platform.system", return_value="Windows"), patch(
        "platform.release", return_value="10"
    ), patch("aikido_zen.helpers.get_machine_ip.get_ip", return_value="192.168.1.1"):
        connection_manager_info = get_manager_info(mock_connection_manager)

        assert connection_manager_info["os"] == {"name": "Windows", "version": "10"}


def test_get_manager_info_python_implementation():
    mock_connection_manager = MockCloudConnectionManager(
        block=False,
        packages={"package1": {"version": "1.0.0", "supported": True}},
        serverless=False,
    )

    with patch(
        "aikido_zen.helpers.get_machine_ip.get_ip", return_value="192.168.1.1"
    ), patch("platform.python_implementation", return_value="RandomPython"):
        connection_manager_info = get_manager_info(mock_connection_manager)

        assert connection_manager_info["platform"]["name"] == "RandomPython"


def test_get_manager_info_with_different_os():
    mock_connection_manager = MockCloudConnectionManager(
        block=False,
        packages={"package1": {"version": "1.0.0", "supported": True}},
        serverless=False,
    )

    with patch(
        "aikido_zen.helpers.get_machine_ip.get_ip", return_value="192.168.1.1"
    ), patch("platform.python_version", return_value="0.1.2"):
        connection_manager_info = get_manager_info(mock_connection_manager)

        assert connection_manager_info["platform"]["version"] == "0.1.2"


def test_get_manager_info_with_different_os():
    mock_connection_manager = MockCloudConnectionManager(
        block=False,
        packages={"package1": {"version": "1.0.0", "supported": True}},
        serverless=False,
    )

    with patch(
        "aikido_zen.helpers.get_machine_ip.get_ip", return_value="192.168.1.1"
    ), patch("platform.python_version", return_value="0.1.2"), patch(
        "platform.python_implementation", return_value="RandomPython"
    ):
        connection_manager_info = get_manager_info(mock_connection_manager)

        assert connection_manager_info["platform"] == {
            "name": "RandomPython",
            "version": "0.1.2",
        }
