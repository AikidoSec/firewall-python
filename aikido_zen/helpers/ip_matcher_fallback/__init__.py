"""
Based on https://github.com/demskie/netparser
MIT License - Copyright (c) 2019 alex
"""

from .shared import parse_base_network, sort_networks, summarize_sorted_networks
from .sort import binary_search_for_insertion_index


class IPMatcher:
    def __init__(self, networks=None):
        self.sorted = []
        if networks is not None:
            subnets = []
            for s in networks:
                net = parse_base_network(s, False)
                if net and net.is_valid():
                    subnets.append(net)
            sort_networks(subnets)
            self.sorted = summarize_sorted_networks(subnets)

    def has(self, network):
        """
        Checks if the given IP address is in the list of networks.
        """
        net = parse_base_network(network, False)
        if not net or not net.is_valid():
            return False
        idx = binary_search_for_insertion_index(net, self.sorted)
        if idx < 0:
            return False
        if idx < len(self.sorted) and self.sorted[idx].contains(net):
            return True
        if idx - 1 >= 0 and self.sorted[idx - 1].contains(net):
            return True
        return False

    def add(self, network):
        net = parse_base_network(network, False)
        if not net or not net.is_valid():
            return self
        idx = binary_search_for_insertion_index(net, self.sorted)
        if idx < len(self.sorted) and self.sorted[idx].compare(net) == 0:
            return self
        self.sorted.insert(idx, net)
        return self

    def is_empty(self):
        return len(self.sorted) == 0
