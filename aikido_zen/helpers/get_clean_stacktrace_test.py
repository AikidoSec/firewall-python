import pytest
import pytest
from .get_clean_stacktrace import get_clean_stacktrace


def test_get_clean_stacktrace_no_aikido():
    """Test that the stack trace does not include aikido frames."""

    def dummy_function():
        return get_clean_stacktrace()

    result = dummy_function()

    assert "/site-packages/aikido_zen/" not in result


def test_get_clean_stacktrace_with_aikido():
    """Test that the stack trace includes non-aikido frames."""

    def dummy_function():
        return get_clean_stacktrace()

    result = dummy_function()
