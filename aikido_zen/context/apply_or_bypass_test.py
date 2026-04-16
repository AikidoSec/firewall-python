import pytest

from aikido_zen.context import current_context, get_current_context
from aikido_zen.context.apply_or_bypass import apply_context_or_bypass
from aikido_zen.storage import bypassed_context_store
from aikido_zen.test_utils.context_utils import generate_context
from aikido_zen.thread.thread_cache import get_cache


@pytest.fixture(autouse=True)
def _reset_state():
    yield
    current_context.set(None)
    bypassed_context_store.clear()
    cache = get_cache()
    if cache:
        cache.reset()


def _set_bypass_list(ips):
    cache = get_cache()
    cache.config.bypassed_ips = _IPMatcherStub(ips)


class _IPMatcherStub:
    def __init__(self, ips):
        self._ips = set(ips)

    def has(self, ip):
        return ip in self._ips


def test_non_bypassed_ip_sets_context_and_clears_flag():
    _set_bypass_list({"9.9.9.9"})
    bypassed_context_store.set_bypassed(True)  # stale value from previous request

    ctx = generate_context(ip="1.2.3.4")
    apply_context_or_bypass(ctx)

    assert get_current_context() is ctx
    assert bypassed_context_store.is_bypassed() is False


def test_bypassed_ip_clears_context_and_sets_flag():
    _set_bypass_list({"1.2.3.4"})

    ctx = generate_context(ip="1.2.3.4")
    apply_context_or_bypass(ctx)

    assert get_current_context() is None
    assert bypassed_context_store.is_bypassed() is True


def test_no_remote_address_falls_through_to_set_context():
    _set_bypass_list({"1.2.3.4"})

    ctx = generate_context()
    ctx.remote_address = None
    apply_context_or_bypass(ctx)

    assert get_current_context() is ctx
    assert bypassed_context_store.is_bypassed() is False


def test_bypass_then_non_bypass_resets_flag():
    _set_bypass_list({"1.2.3.4"})

    ctx_bypassed = generate_context(ip="1.2.3.4")
    apply_context_or_bypass(ctx_bypassed)
    assert bypassed_context_store.is_bypassed() is True

    ctx_normal = generate_context(ip="9.9.9.9")
    apply_context_or_bypass(ctx_normal)
    assert get_current_context() is ctx_normal
    assert bypassed_context_store.is_bypassed() is False
