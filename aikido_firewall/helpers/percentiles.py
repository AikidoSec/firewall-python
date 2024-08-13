"""Exports percentiles function"""

import math


def percentiles(_percentiles, lst):
    """Calculate the specified percentiles from the list."""
    if len(lst) == 0:
        raise ValueError("List should not be empty")

    for p in _percentiles:
        if p < 0:
            raise ValueError(f'Expect percentile to be >= 0 but given "{p}".')

        if p > 100:
            raise ValueError(f'Expect percentile to be <= 100 but given "{p}".')

    sorted_list = sorted(lst)

    return [get_percentile_value(p, sorted_list) for p in _percentiles]


def get_percentile_value(p, lst):
    """Get the value at the specified percentile from the sorted list."""
    if p == 0:
        return lst[0]

    k_index = math.ceil(len(lst) * (p / 100)) - 1

    return lst[k_index]
