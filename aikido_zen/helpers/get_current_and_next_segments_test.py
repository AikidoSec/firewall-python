import pytest
from aikido_zen.helpers.get_current_and_next_segments import (
    get_current_and_next_segments,
)


def test_empty_array():
    assert get_current_and_next_segments([]) == []


def test_single_item_array():
    assert get_current_and_next_segments(["a"]) == []


def test_two_item_array():
    assert get_current_and_next_segments(["a", "b"]) == [("a", "b")]


def test_three_item_array():
    assert get_current_and_next_segments(["a", "b", "c"]) == [("a", "b"), ("b", "c")]


def test_four_item_array():
    assert get_current_and_next_segments(["a", "b", "c", "d"]) == [
        ("a", "b"),
        ("b", "c"),
        ("c", "d"),
    ]
