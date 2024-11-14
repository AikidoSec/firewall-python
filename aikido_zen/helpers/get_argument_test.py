import pytest
from .get_argument import get_argument


def test_get_argument_with_only_kwargs():
    """Test when only kwargs are provided."""
    result = get_argument((), {"arg1": "value1"}, 0, "arg1")
    assert result == "value1", f"Expected 'value1', got {result}"


def test_get_argument_with_only_args():
    """Test when only args are provided."""
    result = get_argument(("value2",), {}, 0, "arg1")
    assert result == "value2", f"Expected 'value2', got {result}"


def test_get_argument_with_args_and_kwargs():
    """Test when both args and kwargs are provided, with priority to kwargs."""
    result = get_argument(("value2",), {"arg1": "value1"}, 0, "arg1")
    assert result == "value1", f"Expected 'value1', got {result}"


def test_get_argument_with_positional_index():
    """Test when args are provided and a specific position is requested."""
    result = get_argument(("value2", "value3"), {}, 1, "arg1")
    assert result == "value3", f"Expected 'value3', got {result}"


def test_get_argument_with_positional_index_out_of_bounds():
    """Test when the positional index is out of bounds."""
    result = get_argument(("value2",), {}, 1, "arg1")
    assert result is None, f"Expected None, got {result}"


def test_get_argument_with_none_in_kwargs():
    """Test when the argument in kwargs is None."""
    result = get_argument((), {"arg1": None}, 0, "arg1")
    assert result is None, f"Expected None, got {result}"


def test_get_argument_with_none_in_args():
    """Test when the argument in args is None."""
    result = get_argument((None,), {}, 0, "arg1")
    assert result is None, f"Expected None, got {result}"


def test_get_argument_with_empty_args_and_kwargs():
    """Test when both args and kwargs are empty."""
    result = get_argument((), {}, 0, "arg1")
    assert result is None, f"Expected None, got {result}"


def test_get_argument_with_multiple_kwargs():
    """Test when multiple kwargs are provided."""
    result = get_argument((), {"arg1": "value1", "arg2": "value2"}, 0, "arg1")
    assert result == "value1", f"Expected 'value1', got {result}"


def test_get_argument_with_positional_index_and_kwargs():
    """Test when both args and kwargs are provided, with positional index."""
    result = get_argument(("value2", "value3"), {"arg1": "value1"}, 0, "arg1")
    assert result == "value1", f"Expected 'value1', got {result}"
