from unittest.mock import patch, MagicMock

import pytest
from aikido_zen.context import current_context, Context, get_current_context
from aikido_zen.thread.thread_cache import ThreadCache, threadlocal_storage
from . import should_block_request


@pytest.fixture(autouse=True)
def run_around_tests():
    yield
    # Make sure to reset context and cache after every test so it does not
    # interfere with other tests
    current_context.set(None)


def test_without_context():
    current_context.set(None)
    assert should_block_request() == {"block": False}


def set_context(user=None, executed_middleware=False):
    Context(
        context_obj={
            "remote_address": "::1",
            "method": "POST",
            "url": "http://localhost:4000",
            "query": {
                "abc": "def",
            },
            "headers": {},
            "body": None,
            "cookies": {},
            "source": "flask",
            "route": "/posts/:id",
            "user": user,
            "executed_middleware": executed_middleware,
        }
    ).set_as_current_context()


class MyThreadCache(ThreadCache):
    def renew_if_ttl_expired(self):
        return


def test_with_context_without_cache():
    set_context()
    threadlocal_storage.cache = None
    assert should_block_request() == {"block": False}


def test_with_context_with_cache():
    set_context(user={"id": "123"})
    thread_cache = MyThreadCache()

    thread_cache.config.blocked_uids = ["123"]
    assert get_current_context().executed_middleware == False
    assert should_block_request() == {
        "block": True,
        "trigger": "user",
        "type": "blocked",
    }
    assert get_current_context().executed_middleware == True

    thread_cache.config.blocked_uids = []
    assert should_block_request() == {"block": False}

    thread_cache.config.blocked_uids = ["23", "234", "456"]
    assert should_block_request() == {"block": False}
    assert get_current_context().executed_middleware == True


def test_cache_comms_with_endpoints():
    set_context(user={"id": "456"})
    thread_cache = MyThreadCache()
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
    assert get_current_context().executed_middleware == False

    with patch("aikido_zen.background_process.comms.get_comms") as mock_get_comms:
        mock_get_comms.return_value = None  # Set the return value of get_comms
        assert should_block_request() == {"block": False}
    assert get_current_context().executed_middleware == True

    with patch("aikido_zen.background_process.comms.get_comms") as mock_get_comms:
        mock_comms = MagicMock()
        mock_get_comms.return_value = mock_comms  # Set the return value of get_comms

        # No matching endpoints :
        assert should_block_request() == {"block": False}
        mock_comms.send_data_to_bg_process.assert_not_called()

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

    with patch("aikido_zen.background_process.comms.get_comms") as mock_get_comms:
        mock_comms = MagicMock()
        mock_get_comms.return_value = mock_comms  # Set the return value of get_comms

        # Rate-limiting disabled:
        assert should_block_request() == {"block": False}
        mock_comms.send_data_to_bg_process.assert_not_called()

    # Enable ratelimiting
    thread_cache.config.endpoints[1]["rateLimiting"]["enabled"] = True

    with patch("aikido_zen.background_process.comms.get_comms") as mock_get_comms:
        mock_comms = MagicMock()
        mock_get_comms.return_value = mock_comms  # Set the return value of get_comms
        mock_comms.send_data_to_bg_process.return_value = {"success": False}

        assert should_block_request() == {"block": False}
        mock_comms.send_data_to_bg_process.assert_called_with(
            action="SHOULD_RATELIMIT",
            obj={
                "route_metadata": {
                    "method": "POST",
                    "route": "/posts/:id",
                    "url": "http://localhost:4000",
                },
                "user": {"id": "456"},
                "remote_address": "::1",
            },
            receive=True,
        )

        mock_comms.send_data_to_bg_process.return_value = {
            "success": True,
            "data": {"block": False, "trigger": "my_trigger"},
        }
        assert should_block_request() == {"block": False}

        mock_comms.send_data_to_bg_process.return_value = {
            "success": True,
            "data": {"block": True, "trigger": "my_trigger"},
        }
        assert should_block_request() == {
            "block": True,
            "ip": "::1",
            "type": "ratelimited",
            "trigger": "my_trigger",
        }
