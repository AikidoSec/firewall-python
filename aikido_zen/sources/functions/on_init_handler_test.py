import pytest

from aikido_zen.background_process.service_config import ServiceConfig
from .on_init_handler import on_init_handler
from ...context import Context, current_context
from aikido_zen.helpers.add_ip_address_to_blocklist import add_ip_address_to_blocklist
from ...thread.thread_cache import ThreadCache, threadlocal_storage
from aikido_zen.helpers.iplist import IPList


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
    config = ServiceConfig(
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
    )
    if blocked_ips:
        config.set_blocked_ips(blocked_ips)
    ThreadCache().config = config
    return config


@pytest.fixture(autouse=True)
def run_around_tests():
    yield
    # Make sure to reset context and cache after every test so it does not
    # interfere with other tests
    current_context.set(None)
    threadlocal_storage.cache = None


def test_blocked_ip():
    # Arrange
    context = set_context("1.1.1.1")
    blocked_ips = [
        {"source": "test", "description": "Blocked for testing", "ips": ["1.1.1.1"]}
    ]
    config = create_service_config(blocked_ips)

    # Act
    result = on_init_handler(context)

    # Assert
    assert result.blocking
    assert (
        result.message
        == "Your IP address is blocked due to Blocked for testing (Your IP: 1.1.1.1)"
    )
    assert result.status_code == 403


def test_allowed_ip():
    # Arrange
    context = set_context("1.1.1.1")
    blocked_ips = [
        {"source": "test", "description": "Blocked for testing", "ips": ["192.168.1.1"]}
    ]
    config = create_service_config(blocked_ips)

    # Act
    result = on_init_handler(context)

    # Assert
    assert not result.blocking


def test_invalid_context():
    # Arrange
    context = None
    config = create_service_config()

    # Act
    result = on_init_handler(context)

    # Assert
    assert not result.blocking


def test_not_allowed_ip():
    # Arrange
    context = set_context("192.168.1.3")
    blocked_ips = [
        {"source": "test", "description": "Blocked for testing", "ips": ["192.168.1.1"]}
    ]
    config = create_service_config(blocked_ips)

    # Act
    result = on_init_handler(context)

    # Assert
    assert result.blocking
    assert (
        result.message
        == "Your IP address is not allowed to access this resource. (Your IP: 192.168.1.3)"
    )
    assert result.status_code == 403


def test_bypassed_ip():
    # Arrange
    context = set_context("1.1.1.1")  # This IP is in the allowed list
    blocked_ips = [
        {"source": "test", "description": "Blocked for testing", "ips": ["192.168.1.1"]}
    ]
    config = create_service_config(blocked_ips)
    add_ip_address_to_blocklist("1.1.1.1", config.bypassed_ips)  # Adding to bypass list

    # Act
    result = on_init_handler(context)

    # Assert
    assert not result.blocking  # Should be allowed since it's in the bypass list


def test_ip_allowed_by_endpoint():
    # Arrange
    context = set_context("2.2.2.2")  # This IP is in the allowed list
    blocked_ips = [
        {"source": "test", "description": "Blocked for testing", "ips": ["192.168.1.1"]}
    ]
    config = create_service_config(blocked_ips)

    # Act
    result = on_init_handler(context)

    # Assert
    assert not result.blocking


def test_ip_not_allowed_by_endpoint():
    # Arrange
    context = set_context("4.4.4.4")  # Not in the allowed list
    blocked_ips = [
        {"source": "test", "description": "Blocked for testing", "ips": ["192.168.1.1"]}
    ]
    config = create_service_config(blocked_ips)

    # Act
    result = on_init_handler(context)

    # Assert
    assert result.blocking
    assert (
        result.message
        == "Your IP address is not allowed to access this resource. (Your IP: 4.4.4.4)"
    )
    assert result.status_code == 403


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
    result = on_init_handler(context)

    # Assert
    assert result.blocking
    assert (
        result.message
        == "Your IP address is not allowed to access this resource. (Your IP: 192.168.1.1)"
    )
    assert result.status_code == 403
