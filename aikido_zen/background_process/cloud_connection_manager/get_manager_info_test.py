import pytest
import socket
from unittest.mock import MagicMock, patch
from .get_manager_info import get_manager_info


# Sample connection_manager object for testing
class MockCloudConnectionManager:
    def __init__(self, block, serverless):
        self.block = block
        self.serverless = serverless


@pytest.fixture
def mock_connection_manager():
    return MockCloudConnectionManager(
        block=True,
        serverless="lambda",
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
    patch1,
    patch2,
    patch3,
    mock_connection_manager,
):
    connection_manager_info = get_manager_info(mock_connection_manager)
    assert connection_manager_info["dryMode"] is False
    assert connection_manager_info["hostname"] == "test-hostname"
    assert connection_manager_info["version"] == "PKG_VERSION"
    assert connection_manager_info["library"] == "firewall-python"
    assert connection_manager_info["ipAddress"] == "192.168.1.1"
    assert connection_manager_info["serverless"] is True
    assert connection_manager_info["stack"] == ["lambda"]
    assert connection_manager_info["os"] == {"name": "Linux", "version": "5.4.0"}
    assert connection_manager_info["preventedPrototypePollution"] is False
    assert connection_manager_info["nodeEnv"] == ""


def test_get_manager_info_with_unsupported_packages():
    mock_connection_manager = MockCloudConnectionManager(
        block=False,
        serverless=None,
    )

    with patch("platform.system", return_value="Linux"), patch(
        "platform.release", return_value="5.4.0"
    ), patch("aikido_zen.helpers.get_machine_ip.get_ip", return_value="192.168.1.1"):
        connection_manager_info = get_manager_info(mock_connection_manager)

        assert connection_manager_info["stack"] == []


def test_get_manager_info_with_non_serverless():
    mock_connection_manager = MockCloudConnectionManager(
        block=False,
        serverless=None,
    )

    with patch("platform.system", return_value="Linux"), patch(
        "platform.release", return_value="5.4.0"
    ), patch("aikido_zen.helpers.get_machine_ip.get_ip", return_value="192.168.1.1"):
        connection_manager_info = get_manager_info(mock_connection_manager)

        assert connection_manager_info["serverless"] is False
        assert connection_manager_info["stack"] == []


def test_get_manager_info_with_blocked_connection_manager():
    mock_connection_manager = MockCloudConnectionManager(
        block=True,
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
        serverless=False,
    )

    with patch(
        "aikido_zen.helpers.get_machine_ip.get_ip", return_value="192.168.1.1"
    ), patch("platform.python_implementation", return_value="RandomPython"):
        connection_manager_info = get_manager_info(mock_connection_manager)

        assert connection_manager_info["platform"]["name"] == "RandomPython"


def test_get_manager_info_with_different_os_2():
    mock_connection_manager = MockCloudConnectionManager(
        block=False,
        serverless=False,
    )

    with patch(
        "aikido_zen.helpers.get_machine_ip.get_ip", return_value="192.168.1.1"
    ), patch("platform.python_version", return_value="0.1.2"):
        connection_manager_info = get_manager_info(mock_connection_manager)

        assert connection_manager_info["platform"]["version"] == "0.1.2"


def test_get_manager_info_with_different_os_3():
    mock_connection_manager = MockCloudConnectionManager(
        block=False,
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
