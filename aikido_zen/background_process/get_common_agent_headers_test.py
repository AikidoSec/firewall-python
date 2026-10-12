import socket
from unittest.mock import MagicMock

import pytest

import aikido_zen.config as config
import aikido_zen.background_process.get_common_agent_headers as headers_module
from aikido_zen.background_process.get_common_agent_headers import (
    get_common_agent_headers,
)
from aikido_zen.helpers.get_agent_session_id import get_agent_session_id
from aikido_zen.helpers.get_hostname import get_hostname
from aikido_zen.helpers.get_machine_ip import get_ip
from aikido_zen.background_process.cloud_connection_manager.get_manager_info import (
    get_manager_info,
)


@pytest.fixture(autouse=True)
def reset_cached_instance_values():
    get_ip.cache_clear()
    get_hostname.cache_clear()


def test_common_agent_headers(monkeypatch):
    monkeypatch.setattr(headers_module, "get_ip", lambda: "10.0.0.1")

    assert get_common_agent_headers() == {
        "X-Agent-Platform": "python",
        "X-Agent-Library": config.LIBRARY_NAME,
        "X-Agent-Version": config.PKG_VERSION,
        "X-Agent-Hostname": get_hostname() or "unknown",
        "X-Agent-IP-Address": "10.0.0.1",
        "X-Agent-Session-Id": get_agent_session_id(),
    }


def test_common_agent_headers_keep_the_same_session_id():
    assert (
        get_common_agent_headers()["X-Agent-Session-Id"]
        == get_common_agent_headers()["X-Agent-Session-Id"]
    )


def test_hostname_and_ip_match_the_event_payload(monkeypatch):
    monkeypatch.setattr(socket, "gethostname", lambda: "instance-app-7c9d")
    monkeypatch.setattr(socket, "gethostbyname", lambda _hostname: "10.0.1.42")
    manager_info = get_manager_info(MagicMock())
    headers = get_common_agent_headers()

    assert headers["X-Agent-Hostname"] == manager_info["hostname"]
    assert headers["X-Agent-IP-Address"] == manager_info["ipAddress"]


def test_hostname_that_cannot_be_a_header_is_unknown(monkeypatch):
    monkeypatch.setattr(socket, "gethostname", lambda: "p\u0101yments")

    assert get_common_agent_headers()["X-Agent-Hostname"] == "unknown"


def test_missing_hostname_is_unknown(monkeypatch):
    monkeypatch.setattr(socket, "gethostname", lambda: "")

    assert get_common_agent_headers()["X-Agent-Hostname"] == "unknown"


def test_unresolved_ip_address_is_unknown(monkeypatch):
    monkeypatch.setattr(headers_module, "get_ip", lambda: "")

    assert get_common_agent_headers()["X-Agent-IP-Address"] == "unknown"


def test_library_matches_the_event_payload():
    assert (
        get_common_agent_headers()["X-Agent-Library"]
        == get_manager_info(MagicMock())["library"]
    )
