import pytest
from .percentiles import percentiles


def generate_array_simple(amount):
    return [i + 1 for i in range(amount)]


def shuffle_array(arr):
    import random

    random.shuffle(arr)
    return arr


stubs_simple = [
    {"percentile": 0, "list": shuffle_array(generate_array_simple(100)), "result": 1},
    {"percentile": 25, "list": shuffle_array(generate_array_simple(100)), "result": 25},
    {"percentile": 50, "list": shuffle_array(generate_array_simple(100)), "result": 50},
    {"percentile": 75, "list": shuffle_array(generate_array_simple(100)), "result": 75},
    {
        "percentile": 100,
        "list": shuffle_array(generate_array_simple(100)),
        "result": 100,
    },
    {
        "percentile": 75,
        "list": shuffle_array(generate_array_simple(100) + generate_array_simple(30)),
        "result": 68,
    },
]


def test_percentile_of_simple_values():
    for stub in stubs_simple:
        assert percentiles([stub["percentile"]], stub["list"]) == [stub["result"]]


def test_percentile_with_negative_values():
    assert percentiles([50], shuffle_array([-1, -2, -3, -4, -5])) == [-3]
    assert percentiles([50], shuffle_array([7, 6, -1, -2, -3, -4, -5])) == [-2]


def test_array_of_percentiles():
    assert percentiles(
        [0, 25, 50, 75, 100], shuffle_array(generate_array_simple(100))
    ) == [1, 25, 50, 75, 100]


def test_throw_error_if_less_than_zero():
    with pytest.raises(ValueError):
        percentiles([-1], [1])


def test_throw_error_if_greater_than_100():
    with pytest.raises(ValueError):
        percentiles([101], [1])


def test_empty_list():
    with pytest.raises(ValueError):
        percentiles([50], [])
