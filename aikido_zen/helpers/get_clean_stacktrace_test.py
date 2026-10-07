import gc
import weakref
from types import SimpleNamespace

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


@pytest.mark.parametrize("formatting_error", [False, True])
def test_get_clean_stacktrace_releases_caller_locals(monkeypatch, formatting_error):
    class Payload:
        pass

    class FailingModuleFilter:
        def __contains__(self, name):
            raise RuntimeError("formatting failed")

    if formatting_error:
        monkeypatch.setitem(
            get_clean_stacktrace.__globals__,
            "sys",
            SimpleNamespace(builtin_module_names=FailingModuleFilter()),
        )

    def caller():
        payload = Payload()
        reference = weakref.ref(payload)
        try:
            get_clean_stacktrace()
        except RuntimeError as error:
            assert formatting_error
            assert str(error) == "formatting failed"
        else:
            assert not formatting_error
        return reference

    gc_was_enabled = gc.isenabled()
    gc.disable()
    try:
        reference = caller()
        assert reference() is None
    finally:
        if gc_was_enabled:
            gc.enable()
