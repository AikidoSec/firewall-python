import pytest
from unittest.mock import patch

from aikido_zen.background_process.cloud_connection_manager import (
    CloudConnectionManager,
)
from .update_firewall_lists import update_firewall_lists
from ...helpers.is_ip_allowed_by_allowlist import is_ip_allowed_by_allowlist


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
    assert connection_manager.conf.is_blocked_ip("192.168.1.1")
    assert connection_manager.conf.is_blocked_ip("192.168.1.2")

    # Check that the allowed IPs were set correctly
    assert is_ip_allowed_by_allowlist(connection_manager.conf, "192.168.1.3")
    assert is_ip_allowed_by_allowlist(connection_manager.conf, "192.168.2.50")

    # Check that the blocked user agents were set correctly
    assert connection_manager.conf.is_user_agent_blocked("bAdBoT test woop wop")
    assert not connection_manager.conf.is_user_agent_blocked("")
    assert not connection_manager.conf.is_user_agent_blocked(None)


def test_update_firewall_lists_no_ua(connection_manager):
    # Call the function to test
    connection_manager.api = MockApiNoUA()
    update_firewall_lists(connection_manager)

    # Check that the blocked IPs were set correctly
    assert connection_manager.conf.is_blocked_ip("192.168.1.1")
    assert connection_manager.conf.is_blocked_ip("192.168.1.2")

    # Check that the blocked user agents were set correctly
    assert not connection_manager.conf.is_user_agent_blocked("bAdBoT test woop wop")
    assert not connection_manager.conf.is_user_agent_blocked("")
    assert connection_manager.conf.blocked_user_agent_regex is None


def test_update_firewall_lists_invalid_regex(connection_manager):
    # Call the function to test
    connection_manager.api = MockApiInvalidRegex()
    update_firewall_lists(connection_manager)

    # Check that the blocked IPs were set correctly
    assert connection_manager.conf.is_blocked_ip("192.168.1.1")
    assert connection_manager.conf.is_blocked_ip("192.168.1.2")

    # Check that the blocked user agents were set correctly
    assert not connection_manager.conf.is_user_agent_blocked("bAdBoT test woop wop")
    assert not connection_manager.conf.is_user_agent_blocked("")
    assert connection_manager.conf.blocked_user_agent_regex is None


def test_update_firewall_lists_no_token(connection_manager):
    # Set token to None
    connection_manager.token = None
    update_firewall_lists(connection_manager)
    # No changes should be made, so we check the initial state
    assert len(connection_manager.conf.bypassed_ips.blocked_subnets) == 0
    assert len(connection_manager.conf.bypassed_ips.blocked_addresses) == 0


def test_update_firewall_lists_serverless(connection_manager):
    # Set serverless to True
    connection_manager.serverless = True
    update_firewall_lists(connection_manager)
    # No changes should be made, so we check the initial state
    assert len(connection_manager.conf.bypassed_ips.blocked_subnets) == 0
    assert len(connection_manager.conf.bypassed_ips.blocked_addresses) == 0


def test_update_firewall_lists_api_failure(connection_manager):
    # Override the mock API to simulate a failure
    class FailingApi:
        def fetch_firewall_lists(self, token):
            return {"success": False}

    connection_manager.api = FailingApi()
    update_firewall_lists(connection_manager)
    # No changes should be made, so we check the initial state
    assert len(connection_manager.conf.bypassed_ips.blocked_subnets) == 0
    assert len(connection_manager.conf.bypassed_ips.blocked_addresses) == 0


def test_update_firewall_lists_exception_handling(connection_manager):
    # Override the mock API to raise an exception
    class ExceptionApi:
        def fetch_firewall_lists(self, token):
            raise Exception("API error")

    connection_manager.api = ExceptionApi()
    update_firewall_lists(connection_manager)
    # No changes should be made, so we check the initial state
    assert len(connection_manager.conf.bypassed_ips.blocked_subnets) == 0
    assert len(connection_manager.conf.bypassed_ips.blocked_addresses) == 0
