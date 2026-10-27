from unittest.mock import patch, MagicMock

import pytest
import aikido_zen.test_utils as test_utils
from aikido_zen.context import current_context, get_current_context
from aikido_zen.thread.thread_cache import get_cache
from . import should_block_request
from .. import set_rate_limit_group


@pytest.fixture(autouse=True)
def run_around_tests():
    get_cache().reset()
    yield
    # Make sure to reset context and cache after every test so it does not
    # interfere with other tests
    current_context.set(None)
    get_cache().reset()


def test_without_context():
    current_context.set(None)
    assert should_block_request() == {"block": False}


def test_with_context_without_cache():
    test_utils.generate_and_set_context()
    get_cache().cache = None
    assert should_block_request() == {"block": False}


def test_with_context_with_cache():
    test_utils.generate_and_set_context(user={"id": "123"})
    thread_cache = get_cache()

    thread_cache.config.blocked_uids = ["123"]
    assert get_current_context().executed_middleware == False
    assert thread_cache.middleware_installed == False
    assert should_block_request() == {
        "block": True,
        "trigger": "user",
        "type": "blocked",
    }
    assert get_current_context().executed_middleware == True
    assert thread_cache.middleware_installed == True
    assert thread_cache.stats.rate_limited_hits == 0

    thread_cache.config.blocked_uids = []
    assert should_block_request() == {"block": False}

    thread_cache.config.blocked_uids = ["23", "234", "456"]
    assert should_block_request() == {"block": False}
    assert get_current_context().executed_middleware == True
    assert thread_cache.middleware_installed == True
    assert thread_cache.stats.rate_limited_hits == 0


def test_bypassed_ip_skips_user_blocking():
    test_utils.generate_and_set_context(user={"id": "123"}, ip="1.2.3.4")
    thread_cache = get_cache()
    thread_cache.config.blocked_uids = ["123"]
    thread_cache.config.set_bypassed_ips(["1.2.3.4"])

    assert should_block_request() == {"block": False}


def test_cache_ipc_with_endpoints():
    test_utils.generate_and_set_context(user={"id": "456"}, route="/posts/:id")
    set_rate_limit_group("my_group")
    thread_cache = get_cache()
    thread_cache.config.blocked_uids = ["123"]
    thread_cache.config.endpoints = [
        {
            "method": "POST",
            "route": "/login",
            "forceProtectionOff": False,
            "rateLimiting": {
                "enabled": True,
                "maxRequests": 3,
                "windowSizeInMS": 1000,
            },
        }
    ]
    thread_cache.config.last_updated_at = 1
    assert get_current_context().executed_middleware == False
    assert thread_cache.middleware_installed == False

    with patch("aikido_zen.background_process.ipc.IPCClient.get") as mock_get_ipc:
        mock_get_ipc.return_value = None  # Set the return value of get_ipc
        assert should_block_request() == {"block": False}
    assert get_current_context().executed_middleware == True
    assert thread_cache.middleware_installed == True

    with patch("aikido_zen.background_process.ipc.IPCClient.get") as mock_get_ipc:
        mock_ipc = MagicMock()
        mock_get_ipc.return_value = mock_ipc  # Set the return value of get_ipc

        # No matching endpoints :
        assert should_block_request() == {"block": False}
        mock_ipc.send_message.assert_not_called()

    thread_cache.config.endpoints.append(
        {
            "method": "POST",
            "route": "/posts/:id",
            "forceProtectionOff": False,
            "rateLimiting": {
                "enabled": False,
                "maxRequests": 3,
                "windowSizeInMS": 1000,
            },
        }
    )

    with patch("aikido_zen.background_process.ipc.IPCClient.get") as mock_get_ipc:
        mock_ipc = MagicMock()
        mock_get_ipc.return_value = mock_ipc  # Set the return value of get_ipc

        # Rate-limiting disabled:
        assert should_block_request() == {"block": False}
        mock_ipc.send_message.assert_not_called()

    # Enable ratelimiting
    thread_cache.config.endpoints[1]["rateLimiting"]["enabled"] = True

    with patch("aikido_zen.background_process.ipc.IPCClient.get") as mock_get_ipc:
        mock_ipc = MagicMock()
        mock_get_ipc.return_value = mock_ipc  # Set the return value of get_ipc
        mock_ipc.send_message.return_value = {"success": False}

        assert should_block_request() == {"block": False}
        mock_ipc.send_message.assert_called()
        (message,) = mock_ipc.send_message.call_args.args
        assert message.identifier == "SHOULD_RATELIMIT"
        assert message.timeout_in_sec == 0.01
        assert message.request == {
            "route_metadata": {
                "method": "POST",
                "route": "/posts/:id",
                "url": "http://localhost:8080/",
            },
            "user": {"id": "456"},
            "group": "my_group",
            "remote_address": "1.1.1.1",
        }

        mock_ipc.send_message.return_value = {
            "success": True,
            "data": {"block": False, "trigger": "my_trigger"},
        }
        assert should_block_request() == {"block": False}

        mock_ipc.send_message.return_value = {
            "success": True,
            "data": {"block": True, "trigger": "my_trigger"},
        }
        assert thread_cache.stats.rate_limited_hits == 0
        assert should_block_request() == {
            "block": True,
            "ip": "1.1.1.1",
            "type": "ratelimited",
            "trigger": "my_trigger",
            "retry_after_seconds": None,
        }
        assert thread_cache.stats.rate_limited_hits == 1

        mock_comms.send_data_to_bg_process.return_value = {
            "success": True,
            "data": {"block": True, "trigger": "my_trigger", "retry_after_seconds": 7},
        }
        assert should_block_request() == {
            "block": True,
            "ip": "1.1.1.1",
            "type": "ratelimited",
            "trigger": "my_trigger",
            "retry_after_seconds": 7,
        }
        assert thread_cache.stats.rate_limited_hits == 2
