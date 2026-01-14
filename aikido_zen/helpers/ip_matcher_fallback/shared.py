"""
Based on https://github.com/demskie/netparser
MIT License - Copyright (c) 2019 alex
"""

import math
from .sort import native_sort
from .network import Network


def sort_networks(networks):
    return native_sort(networks)


def increase_size_by_one_bit(network):
    current_cidr = network.cidr()
    if math.isnan(current_cidr) or current_cidr <= 0:
        return network  # Can't increase size further, or network is invalid
    wider = network.set_cidr(current_cidr - 1)
    wider.addr.apply_subnet_mask(wider.cidr())
    return wider


def summarize_sorted_networks(sorted_networks):
    if not sorted_networks:
        return []
    summarized = sorted_networks[:1]  # Copy the first element
    for idx in range(1, len(sorted_networks)):
        current_network = sorted_networks[idx]
        if len(summarized) == 0:
            summarized.append(current_network)
            continue
        if summarized[-1].contains(current_network):
            continue
        summarized.append(current_network)
        while len(summarized) >= 2:
            a = summarized[-2]
            b = summarized[-1]
            a_cidr = a.cidr()
            b_cidr = b.cidr()
            # Handle NaN cases for cidr() and ensure CIDRs are equal and valid
            if (
                math.isnan(a_cidr)
                or math.isnan(b_cidr)
                or a_cidr != b_cidr
                or a_cidr <= 0  # Can't decrease CIDR if it's already <= 0
                or not a.addr.is_base_address(a_cidr - 1)
                or not a.adjacent(b)
            ):
                break
            increase_size_by_one_bit(a)
            summarized.pop()
    return summarized


def parse_base_network(s, strict=False):
    net = Network(s)
    if not net.is_valid():
        return None
    if not strict:
        net.addr.apply_subnet_mask(net.cidr())
    else:
        original = net.addr.duplicate()
        net.addr.apply_subnet_mask(net.cidr())
        if not net.addr.equals(original):
            return None
    return net
