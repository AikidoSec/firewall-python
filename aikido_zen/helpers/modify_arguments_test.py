import pytest
from .modify_arguments import modify_arguments


def test_injects_value_as_kwarg():
    args, kwargs = modify_arguments((), {}, 0, "key", "val")
    assert kwargs["key"] == "val"
    assert args == ()


def test_overwrites_positional_arg_at_pos():
    args, kwargs = modify_arguments(("a", "b", "c"), {}, 2, "key", "new")
    assert args == ("a", "b", "new")
    assert "key" not in kwargs


def test_overwrites_positional_arg_keeps_trailing_args():
    args, kwargs = modify_arguments(("a", "b", "c", "d"), {}, 2, "key", "new")
    assert args == ("a", "b", "new", "d")
    assert "key" not in kwargs


def test_injects_as_kwarg_when_pos_not_in_args():
    args, kwargs = modify_arguments(("a", "b"), {}, 5, "key", "new")
    assert args == ("a", "b")
    assert kwargs["key"] == "new"


def test_overwrites_existing_kwarg():
    args, kwargs = modify_arguments((), {"key": "old"}, 0, "key", "new")
    assert kwargs["key"] == "new"


def test_does_not_mutate_original_kwargs():
    original = {"other": 1}
    _, kwargs = modify_arguments((), original, 0, "key", "val")
    assert "key" not in original
    assert kwargs["other"] == 1


def test_does_not_mutate_original_args():
    original = ("a", "b", "c")
    new_args, _ = modify_arguments(original, {}, 1, "key", "val")
    assert original == ("a", "b", "c")
    assert new_args == ("a", "val", "c")


def test_empty_args_and_kwargs():
    args, kwargs = modify_arguments((), {}, 3, "key", 42)
    assert args == ()
    assert kwargs == {"key": 42}


def test_preserves_other_kwargs():
    args, kwargs = modify_arguments((), {"a": 1, "b": 2}, 5, "c", 3)
    assert kwargs["a"] == 1
    assert kwargs["b"] == 2
    assert kwargs["c"] == 3
