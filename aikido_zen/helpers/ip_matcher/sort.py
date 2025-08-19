"""
Based on https://github.com/demskie/netparser
MIT License - Copyright (c) 2019 alex
"""

import math
from functools import cmp_to_key

BEFORE = -1
EQUALS = 0
AFTER = 1


def compare_networks(a, b):
    a_bytes = a.addr.bytes()
    b_bytes = b.addr.bytes()
    if len(a_bytes) != len(b_bytes):
        return len(a_bytes) - len(b_bytes)
    for i in range(len(a_bytes)):
        if a_bytes[i] != b_bytes[i]:
            return a_bytes[i] - b_bytes[i]
    a_cidr = a.cidr()
    b_cidr = b.cidr()
    if math.isnan(a_cidr) and math.isnan(b_cidr):
        return 0
    if math.isnan(a_cidr):
        return -1
    if math.isnan(b_cidr):
        return 1
    return a_cidr - b_cidr


def native_sort(networks):
    networks.sort(key=cmp_to_key(compare_networks))
    return networks


def binary_search_for_insertion_index(network, sorted_networks):
    if not sorted_networks or len(sorted_networks) == 0:
        return 0
    left = 0
    right = len(sorted_networks) - 1
    while left < right:
        middle = left + (right - left) // 2
        cmp_result = sorted_networks[middle].compare(network)
        if cmp_result is None:
            return middle + 1
        if cmp_result == EQUALS:
            return middle + 1
        elif cmp_result == BEFORE:
            left = middle + 1
        else:  # AFTER
            right = middle - 1
    # Now left == right
    cmp_result = sorted_networks[left].compare(network)
    if cmp_result is None:
        return left + 1
    if cmp_result == BEFORE:
        return left + 1
    return left
