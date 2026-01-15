import inspect

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from aikido_zen.background_process.commands import process_check_firewall_lists
from aikido_zen.context import current_context
from aikido_zen.thread.thread_cache import get_cache
from aikido_zen.storage.firewall_lists import FirewallLists
from aikido_zen.sources.functions.asgi_middleware import InternalASGIMiddleware
from aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector import (
    AttackWaveDetector,
)


# --- Fixtures ---
@pytest.fixture(autouse=True)
def run_around_tests():
    get_cache().reset()
    current_context.set(None)
    yield
    get_cache().reset()
    current_context.set(None)


TEST_ASGI_SCOPE = {
    "type": "http",
    "client": ["1.1.1.1"],
    "method": "GET",
    "headers": [],
    "scheme": "http",
    "server": "127.0.0.1",
    "query_string": b"",
}


@pytest.fixture(autouse=True)
def mock_asgi_app():
    class ASGIMock:
        def __init__(self):
            self.called = 0

        async def app(self, scope, receive, send):
            self.called += 1

        def was_called(self):
            return self.called > 0

    return ASGIMock()


class MyMockComms:
    def __init__(self):
        self.firewall_lists = FirewallLists()
        self.conn_manager = MagicMock()
        self.conn_manager.firewall_lists = self.firewall_lists
        self.conn_manager.attack_wave_detector = AttackWaveDetector()
        self.attacks = []

    def send_data_to_bg_process(self, action, obj, receive=False, timeout_in_sec=0.1):
        if action != "CHECK_FIREWALL_LISTS":
            return {"success": False}
        res = process_check_firewall_lists(self.conn_manager, obj)
        return {
            "success": True,
            "data": res,
        }


def patch_firewall_lists(func):
    async def wrapper(*args, **kwargs):
        with patch("aikido_zen.background_process.comms.get_comms") as mock_comms:
            comms = MyMockComms()
            mock_comms.return_value = comms

            sig = inspect.signature(func)
            if "attacks" in sig.parameters:
                kwargs["attacks"] = comms.attacks
            if "firewall_lists" in sig.parameters:
                kwargs["firewall_lists"] = comms.firewall_lists

            return await func(*args, **kwargs)

    return wrapper


# --- Test Cases ---
@pytest.mark.asyncio
async def test_middleware_ignores_non_http_scope(mock_asgi_app):
    middleware = InternalASGIMiddleware(mock_asgi_app.app, "test_source")
    scope = {"type": "websocket"}
    receive = AsyncMock()
    send = AsyncMock()

    assert not mock_asgi_app.was_called()
    await middleware(scope, receive, send)
    assert mock_asgi_app.was_called()

    send.assert_not_called()
    receive.assert_not_called()


@pytest.mark.asyncio
async def test_middleware_bypasses_blocked_ip(mock_asgi_app):
    middleware = InternalASGIMiddleware(mock_asgi_app.app, "test_source")
    scope = {"type": "http", "client": ["192.168.1.1"]}
    receive = AsyncMock()
    send = AsyncMock()

    cache = get_cache()
    cache.config.set_bypassed_ips(["192.168.1.1"])

    await middleware(scope, receive, send)
    assert mock_asgi_app.was_called()


@pytest.mark.asyncio
@patch_firewall_lists
async def test_middleware_blocks_request_if_intercepted(firewall_lists):
    firewall_lists.set_blocked_ips(
        [{"source": "test", "description": "Blocked for testing", "ips": ["1.1.1.1"]}]
    )

    async def app(scope, receive, send):
        pass

    middleware = InternalASGIMiddleware(app, "uvicorn")
    scope = {
        "type": "http",
        "client": ["1.1.1.1"],
        "method": "GET",
        "headers": [],
        "scheme": "http",
        "server": "127.0.0.1",
        "query_string": b"",
    }
    receive = AsyncMock()
    send = AsyncMock()

    await middleware(scope, receive, send)

    send.assert_any_call(
        {
            "type": "http.response.start",
            "status": 403,
            "headers": [(b"content-type", b"text/plain")],
        }
    )
    send.assert_any_call(
        {
            "type": "http.response.body",
            "body": b"Your IP address is blocked due to Blocked for testing (Your IP: 1.1.1.1)",
            "more_body": False,
        }
    )


@pytest.mark.asyncio
async def test_middleware_increments_total_hits(mock_asgi_app):
    middleware = InternalASGIMiddleware(mock_asgi_app.app, "uvicorn")
    receive = AsyncMock()
    send = AsyncMock()

    await middleware(TEST_ASGI_SCOPE, receive, send)
    assert get_cache().stats.total_hits == 1
    assert mock_asgi_app.was_called()
