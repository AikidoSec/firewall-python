import pytest

from aikido_zen.storage import bypassed_context_store


@pytest.fixture(autouse=True)
def _reset_after_each_test():
    yield
    bypassed_context_store.clear()


def test_default_is_false():
    assert bypassed_context_store.is_bypassed() is False


def test_set_bypassed_true_then_false():
    bypassed_context_store.set_bypassed(True)
    assert bypassed_context_store.is_bypassed() is True

    bypassed_context_store.set_bypassed(False)
    assert bypassed_context_store.is_bypassed() is False


def test_clear_resets_to_false():
    bypassed_context_store.set_bypassed(True)
    assert bypassed_context_store.is_bypassed() is True

    bypassed_context_store.clear()
    assert bypassed_context_store.is_bypassed() is False


def test_truthy_values_coerced_to_bool():
    bypassed_context_store.set_bypassed("yes")
    assert bypassed_context_store.is_bypassed() is True

    bypassed_context_store.set_bypassed(0)
    assert bypassed_context_store.is_bypassed() is False
