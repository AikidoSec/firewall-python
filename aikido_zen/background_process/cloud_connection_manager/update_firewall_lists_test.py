import pytest
from unittest.mock import patch

from aikido_zen.background_process.cloud_connection_manager import (
    CloudConnectionManager,
)
from aikido_zen.background_process.commands.check_firewall_lists import (
    process_check_firewall_lists,
)
from .update_firewall_lists import update_firewall_lists


class MockApi:
    """Mock API class to simulate API responses."""

    def fetch_firewall_lists(self, token):
        return {
            "success": True,
            "blockedIPAddresses": [
                {
                    "source": "example",
                    "description": "Example description",
                    "ips": ["192.168.1.0/24"],
                }
            ],
            "allowedIPAddresses": [
                {
                    "source": "list1",
                    "description": "Example description",
                    "ips": ["192.168.1.3"],
                },
                {
                    "source": "example",
                    "description": "Example description",
                    "ips": ["192.168.2.0/24"],
                },
            ],
            "blockedUserAgents": "BadBot|Test",
        }


class MockApiNoUA:
    """Mock API class to simulate API responses."""

    def fetch_firewall_lists(self, token):
        return {
            "success": True,
            "blockedIPAddresses": [
                {
                    "source": "example",
                    "description": "Example description",
                    "ips": ["192.168.1.0/24"],
                }
            ],
            "allowedIPAddresses": [],
            "blockedUserAgents": "",
        }


class MockApiInvalidRegex:
    """Mock API class to simulate API responses."""

    def fetch_firewall_lists(self, token):
        return {
            "success": True,
            "blockedIPAddresses": [
                {
                    "source": "example",
                    "description": "Example description",
                    "ips": ["192.168.1.0/24"],
                }
            ],
            "allowedIPAddresses": [],
            "blockedUserAgents": "[abc",
        }


class MockApiInvalidNetwork:
    """Mock API class to simulate a list with one network that is not valid."""

    def __init__(self, invalid_network):
        self.invalid_network = invalid_network

    def fetch_firewall_lists(self, token):
        return {
            "success": True,
            "blockedIPAddresses": [
                {
                    "source": "new",
                    "description": "Example description",
                    "ips": ["10.0.0.0/8", self.invalid_network],
                }
            ],
            "allowedIPAddresses": [],
            "blockedUserAgents": "NewBot",
        }


@pytest.fixture
def connection_manager():
    """Fixture to create a CloudConnectionManager instance with a mock API."""

    class TestCloudConnectionManager(CloudConnectionManager):
        """A test version of CloudConnectionManager with a mock API."""

        def __init__(self, token, serverless):
            super().__init__(
                block=False, api=MockApi(), token=token, serverless=serverless
            )

    return TestCloudConnectionManager(token="valid_token", serverless=False)


def test_update_firewall_lists_success(connection_manager):
    # Call the function to test
    update_firewall_lists(connection_manager)

    # Check that the blocked IPs were set correctly
    assert connection_manager.firewall_lists.is_blocked_ip("192.168.1.1")
    assert connection_manager.firewall_lists.is_blocked_ip("192.168.1.2")

    # Check that the allowed IPs were set correctly
    assert connection_manager.firewall_lists.is_allowed_ip("192.168.1.3")
    assert connection_manager.firewall_lists.is_allowed_ip("192.168.2.50")

    # Check that the blocked user agents were set correctly
    assert connection_manager.firewall_lists.is_user_agent_blocked(
        "bAdBoT test woop wop"
    )
    assert not connection_manager.firewall_lists.is_user_agent_blocked("")
    assert not connection_manager.firewall_lists.is_user_agent_blocked(None)


def test_update_firewall_lists_keeps_allowed_ips_when_rebuild_fails(
    connection_manager, monkeypatch
):
    update_firewall_lists(connection_manager)
    assert not connection_manager.firewall_lists.is_allowed_ip("1.1.1.1")

    monkeypatch.setattr(
        "aikido_zen.helpers.zen_internals._ip_matcher_create", lambda *args: None
    )
    update_firewall_lists(connection_manager)

    assert not connection_manager.firewall_lists.is_allowed_ip("1.1.1.1")
    assert connection_manager.firewall_lists.is_allowed_ip("192.168.2.50")
    assert connection_manager.firewall_lists.is_blocked_ip("192.168.1.1")


@pytest.mark.parametrize("invalid_network", ["not-a-network", "\udc80.1.1.1"])
def test_update_firewall_lists_skips_invalid_networks_and_logs_them(
    connection_manager, caplog, invalid_network
):
    update_firewall_lists(connection_manager)

    connection_manager.api = MockApiInvalidNetwork(invalid_network)
    update_firewall_lists(connection_manager)

    assert "IP list new has 1 invalid network(s)" in caplog.text
    assert connection_manager.firewall_lists.is_blocked_ip("10.0.0.1")
    assert not connection_manager.firewall_lists.is_blocked_ip("192.168.1.1")
    assert connection_manager.firewall_lists.is_allowed_ip("1.1.1.1")
    assert connection_manager.firewall_lists.is_user_agent_blocked("NewBot")
    assert not connection_manager.firewall_lists.is_user_agent_blocked("BadBot")


@pytest.mark.parametrize(
    "allowed_entry",
    [
        {"source": "list1", "description": "Example description"},
        {"source": "list1", "description": "Example description", "ips": None},
        {"source": "list1", "description": "Example description", "ips": []},
    ],
)
def test_update_firewall_lists_skips_an_allowlist_entry_without_ips(
    connection_manager, allowed_entry
):
    connection_manager.firewall_lists.update(
        [{"source": "new", "description": "Example", "ips": ["10.0.0.0/8"]}],
        [allowed_entry],
        "NewBot",
    )

    assert connection_manager.firewall_lists.is_allowed_ip("8.8.8.8")
    assert connection_manager.firewall_lists.is_blocked_ip("10.0.0.1")
    assert connection_manager.firewall_lists.is_user_agent_blocked("NewBot")


@pytest.mark.parametrize(
    "blocked_entry",
    [
        {"source": "new", "ips": ["10.0.0.0/8"]},
        {"source": "new", "description": "", "ips": ["10.0.0.0/8"]},
    ],
)
def test_update_firewall_lists_blocks_ips_from_a_list_without_description(
    connection_manager, blocked_entry
):
    connection_manager.firewall_lists.update([blocked_entry], [], "")

    result = process_check_firewall_lists(
        connection_manager, {"ip": "10.0.0.1", "user-agent": None}
    )
    assert result == {
        "blocked": True,
        "type": "blocklist",
        "reason": "a firewall list",
    }


def test_update_firewall_lists_without_ip_matcher(connection_manager, monkeypatch):
    monkeypatch.setattr("aikido_zen.helpers.zen_internals._ip_matcher_create", None)

    update_firewall_lists(connection_manager)

    assert not connection_manager.firewall_lists.is_blocked_ip("192.168.1.1")
    assert connection_manager.firewall_lists.is_allowed_ip("1.1.1.1")
    assert connection_manager.firewall_lists.is_user_agent_blocked("BadBot")


def test_update_firewall_lists_no_ua(connection_manager):
    # Call the function to test
    connection_manager.api = MockApiNoUA()
    update_firewall_lists(connection_manager)

    # Check that the blocked IPs were set correctly
    assert connection_manager.firewall_lists.is_blocked_ip("192.168.1.1")
    assert connection_manager.firewall_lists.is_blocked_ip("192.168.1.2")

    # Check that the blocked user agents were set correctly
    assert not connection_manager.firewall_lists.is_user_agent_blocked(
        "bAdBoT test woop wop"
    )
    assert not connection_manager.firewall_lists.is_user_agent_blocked("")
    assert connection_manager.firewall_lists.blocked_user_agent_regex is None


def test_update_firewall_lists_invalid_regex(connection_manager):
    # Call the function to test
    connection_manager.api = MockApiInvalidRegex()
    update_firewall_lists(connection_manager)

    # Check that the blocked IPs were set correctly
    assert connection_manager.firewall_lists.is_blocked_ip("192.168.1.1")
    assert connection_manager.firewall_lists.is_blocked_ip("192.168.1.2")

    # Check that the blocked user agents were set correctly
    assert not connection_manager.firewall_lists.is_user_agent_blocked(
        "bAdBoT test woop wop"
    )
    assert not connection_manager.firewall_lists.is_user_agent_blocked("")
    assert connection_manager.firewall_lists.blocked_user_agent_regex is None


def test_update_firewall_lists_no_token(connection_manager):
    # Set token to None
    connection_manager.token = None
    update_firewall_lists(connection_manager)
    # No changes should be made, so we check the initial state
    assert connection_manager.conf.bypassed_ips.is_empty()


def test_update_firewall_lists_serverless(connection_manager):
    # Set serverless to True
    connection_manager.serverless = True
    update_firewall_lists(connection_manager)
    # No changes should be made, so we check the initial state
    assert connection_manager.conf.bypassed_ips.is_empty()


def test_update_firewall_lists_api_failure(connection_manager):
    # Override the mock API to simulate a failure
    class FailingApi:
        def fetch_firewall_lists(self, token):
            return {"success": False}

    connection_manager.api = FailingApi()
    update_firewall_lists(connection_manager)
    # No changes should be made, so we check the initial state
    assert connection_manager.conf.bypassed_ips.is_empty()


def test_update_firewall_lists_exception_handling(connection_manager):
    # Override the mock API to raise an exception
    class ExceptionApi:
        def fetch_firewall_lists(self, token):
            raise Exception("API error")

    connection_manager.api = ExceptionApi()
    update_firewall_lists(connection_manager)
    # No changes should be made, so we check the initial state
    assert connection_manager.conf.bypassed_ips.is_empty()
