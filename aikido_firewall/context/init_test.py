import pytest
from aikido_firewall.context import Context, get_current_context


def test_get_current_context_no_context():
    # Test get_current_context() when no context is set
    assert get_current_context() is None


def test_set_as_current_context(mocker):
    # Test set_as_current_context() method
    sample_request = mocker.MagicMock()
    context = Context(sample_request)
    context.set_as_current_context()
    assert get_current_context() == context


def test_get_current_context_with_context(mocker):
    # Test get_current_context() when a context is set
    sample_request = mocker.MagicMock()
    context = Context(sample_request)
    context.set_as_current_context()
    assert get_current_context() == context
