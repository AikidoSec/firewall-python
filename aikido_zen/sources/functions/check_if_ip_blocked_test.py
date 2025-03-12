import pytest

from aikido_zen.background_process.service_config import ServiceConfig
from .check_if_ip_blocked import check_if_ip_blocked
from ...context import Context
from aikido_zen.helpers.add_ip_address_to_blocklist import add_ip_address_to_blocklist
from aikido_zen.helpers.blocklist import BlockList


# Helper function to set context
def set_context(remote_address):
    return Context(
        context_obj={
            "remote_address": remote_address,
            "method": "POST",
            "url": "http://localhost:4000",
            "query": {"abc": "def"},
            "headers": {},
            "body": None,
            "cookies": {},
            "source": "flask",
            "route": "/posts/:number",
            "user": None,
            "executed_middleware": False,
        }
    )


# Helper function to create ServiceConfig
def create_service_config(blocked_ips=None):
    return ServiceConfig(
        endpoints=[
            {
                "method": "POST",
                "route": "/posts/:number",
                "graphql": False,
                "allowedIPAddresses": ["1.1.1.1", "2.2.2.2", "3.3.3.3"],
            }
        ],
        last_updated_at=None,
        blocked_uids=set(),
        bypassed_ips=[],
        received_any_stats=False,
        blocked_ips=blocked_ips or [],
    )


def test_blocked_ip():
    # Arrange
    context = set_context("192.168.1.1")
    blocked_ips = [
        {"source": "test", "description": "Blocked for testing", "ips": ["192.168.1.1"]}
    ]
    config = create_service_config(blocked_ips)

    # Act
    result = check_if_ip_blocked(context, config.endpoints, config)

    # Assert
    assert result == (
        "Your IP address is blocked due to Blocked for testing (Your IP: 192.168.1.1)",
        403,
    )


def test_allowed_ip():
    # Arrange
    context = set_context("1.1.1.1")
    blocked_ips = [
        {"source": "test", "description": "Blocked for testing", "ips": ["192.168.1.1"]}
    ]
    config = create_service_config(blocked_ips)

    # Act
    result = check_if_ip_blocked(context, config.endpoints, config)

    # Assert
    assert result is False


def test_invalid_context():
    # Arrange
    context = None
    config = create_service_config()

    # Act
    result = check_if_ip_blocked(context, config.endpoints, config)

    # Assert
    assert result is False


def test_not_allowed_ip():
    # Arrange
    context = set_context("192.168.1.3")
    blocked_ips = [
        {"source": "test", "description": "Blocked for testing", "ips": ["192.168.1.1"]}
    ]
    config = create_service_config(blocked_ips)

    # Act
    result = check_if_ip_blocked(context, config.endpoints, config)

    # Assert
    assert result == (
        "Your IP address is not allowed to access this resource. (Your IP: 192.168.1.3)",
        403,
    )


def test_bypassed_ip():
    # Arrange
    context = set_context("1.1.1.1")  # This IP is in the allowed list
    blocked_ips = [
        {"source": "test", "description": "Blocked for testing", "ips": ["192.168.1.1"]}
    ]
    config = create_service_config(blocked_ips)
    add_ip_address_to_blocklist("1.1.1.1", config.bypassed_ips)  # Adding to bypass list

    # Act
    result = check_if_ip_blocked(context, config.endpoints, config)

    # Assert
    assert result is False  # Should be allowed since it's in the bypass list


def test_ip_allowed_by_endpoint():
    # Arrange
    context = set_context("2.2.2.2")  # This IP is in the allowed list
    blocked_ips = [
        {"source": "test", "description": "Blocked for testing", "ips": ["192.168.1.1"]}
    ]
    config = create_service_config(blocked_ips)

    # Act
    result = check_if_ip_blocked(context, config.endpoints, config)

    # Assert
    assert result is False  # Should be allowed since it's in the allowed list


def test_ip_not_allowed_by_endpoint():
    # Arrange
    context = set_context("4.4.4.4")  # Not in the allowed list
    blocked_ips = [
        {"source": "test", "description": "Blocked for testing", "ips": ["192.168.1.1"]}
    ]
    config = create_service_config(blocked_ips)

    # Act
    result = check_if_ip_blocked(context, config.endpoints, config)

    # Assert
    assert result == (
        "Your IP address is not allowed to access this resource. (Your IP: 4.4.4.4)",
        403,
    )


def test_multiple_blocked_ips():
    # Arrange
    context = set_context("192.168.1.1")  # This IP is blocked
    blocked_ips = [
        {
            "source": "test",
            "description": "Blocked for testing",
            "ips": ["192.168.1.1", "192.168.1.2"],
        }
    ]
    config = create_service_config(blocked_ips)

    # Act
    result = check_if_ip_blocked(context, config.endpoints, config)

    # Assert
    assert result == (
        "Your IP address is blocked due to Blocked for testing (Your IP: 192.168.1.1)",
        403,
    )
