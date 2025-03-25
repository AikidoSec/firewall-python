import pytest
from unittest.mock import MagicMock, patch
from aikido_zen.context import Context, get_current_context, current_context
from .on_init_handler import on_init_handler
from ...thread.thread_cache import ThreadCache, threadlocal_storage


@pytest.fixture
def mock_context():
    """Fixture to create a mock context."""
    context = MagicMock(spec=Context)
    context.remote_address = "192.168.1.1"  # Example IP
    return context


@pytest.fixture(autouse=True)
def run_around_tests():
    current_context.set(None)
    threadlocal_storage.cache = None
    yield
    current_context.set(None)
    threadlocal_storage.cache = None


def test_on_init_handler_with_none_context():
    """Test that the function returns early if context is None."""
    result = on_init_handler(None)
    assert result is None  # No return value, just ensure it doesn't raise an error


def test_on_init_handler_with_bypassed_ip(mock_context):
    """Test that the function returns early if the IP is bypassed."""
    cache = ThreadCache()
    cache.config.set_bypassed_ips(["192.168.1.1"])
    on_init_handler(mock_context)
    mock_context.set_as_current_context.assert_not_called()


def test_on_init_handler_with_valid_context(mock_context):
    """Test that the function processes the context correctly when IP is not bypassed."""
    cache = ThreadCache()
    on_init_handler(mock_context)
    mock_context.set_as_current_context.assert_called_once()  # Should set context
    assert cache.reqs == 1
    on_init_handler(mock_context)
    assert cache.reqs == 2


def test_on_init_handler_with_valid_context_but_empty_thread_cache(mock_context):
    on_init_handler(mock_context)
    mock_context.set_as_current_context.assert_called_once()  # Should set context
