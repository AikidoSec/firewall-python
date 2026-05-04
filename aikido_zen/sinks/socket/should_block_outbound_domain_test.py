import pytest

from aikido_zen.sinks.socket.should_block_outbound_domain import (
    should_block_outbound_domain,
)
from aikido_zen.storage import bypassed_context_store
from aikido_zen.thread.thread_cache import get_cache


@pytest.fixture(autouse=True)
def _reset_state():
    cache = get_cache()
    if cache:
        cache.reset()
    bypassed_context_store.clear()
    yield
    if cache:
        cache.reset()
    bypassed_context_store.clear()


def test_unknown_domain_not_blocked():
    assert should_block_outbound_domain("safe.example.com", 80) is False
    assert any(
        h["hostname"] == "safe.example.com"
        for h in get_cache().hostnames.as_array()
    )


def test_blocked_domain_is_blocked_and_recorded():
    cache = get_cache()
    cache.config.update_outbound_domains([{"hostname": "evil.example.com", "mode": "block"}])

    assert should_block_outbound_domain("evil.example.com", 80) is True
    # Blocked domains are still recorded so they show up in the dashboard.
    assert any(
        h["hostname"] == "evil.example.com"
        for h in cache.hostnames.as_array()
    )


def test_bypassed_request_does_not_block_or_record():
    cache = get_cache()
    cache.config.update_outbound_domains([{"hostname": "evil.example.com", "mode": "block"}])
    bypassed_context_store.set_bypassed(True)

    assert should_block_outbound_domain("evil.example.com", 80) is False
    # No hostname pollution from bypassed-IP requests.
    assert cache.hostnames.as_array() == []


def test_bypassed_request_does_not_record_unknown_domain():
    bypassed_context_store.set_bypassed(True)

    assert should_block_outbound_domain("anything.example.com", 80) is False
    assert get_cache().hostnames.as_array() == []
