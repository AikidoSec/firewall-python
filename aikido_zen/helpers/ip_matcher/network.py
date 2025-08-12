"""
Based on https://github.com/demskie/netparser
MIT License - Copyright (c) 2019 alex
"""

import math
import aikido_zen.helpers.ip_matcher.parse as parse
from .address import Address

BEFORE = -1
EQUALS = 0
AFTER = 1


class Network:
    def __init__(self, network=None):
        self.addr = Address()
        self.netbits = -1
        if network:
            net = parse.network(network)
            if net:
                self.addr.set_bytes(net["bytes"])
                self.netbits = net["cidr"]

    def destroy(self):
        self.addr.destroy()
        self.netbits = -1
        return self

    def cidr(self):
        if self.is_valid():
            return self.netbits
        return float("nan")

    def is_valid(self):
        return self.addr.is_valid() and self.netbits != -1

    def duplicate(self):
        network = Network()
        if self.is_valid():
            network.addr.set_bytes(self.addr.bytes().copy())
            network.netbits = self.netbits
        return network

    def next(self):
        self.addr.increase(self.netbits)
        return self

    def set_cidr(self, cidr):
        if not self.addr.is_valid():
            self.destroy()
        else:
            cidr = math.floor(cidr)
            if cidr >= 0 and cidr <= len(self.addr.bytes()) * 8:
                self.netbits = cidr
            else:
                self.destroy()
        return self

    def compare(self, network):
        if not self.is_valid() or not network.is_valid():
            return None
        cmp = self.addr.compare(network.addr)
        if cmp != EQUALS:
            return cmp
        if self.netbits < network.netbits:
            return BEFORE
        if self.netbits > network.netbits:
            return AFTER
        return EQUALS

    def contains(self, network):
        if not self.is_valid() or not network.is_valid():
            return False
        if len(self.addr.bytes()) != len(network.addr.bytes()):
            return False
        if self.netbits == 0:
            return True
        if network.netbits == 0:
            return False
        if self.addr.compare(network.addr) == AFTER:
            return False
        next_network = self.duplicate().next()
        other_next = network.duplicate().next()
        if not next_network.is_valid():
            return True
        if next_network.addr.compare(other_next.addr) == BEFORE:
            return False
        return True

    def adjacent(self, network):
        if not self.is_valid() or not network.is_valid():
            return False
        if len(self.addr.bytes()) != len(network.addr.bytes()):
            return False
        if self.netbits == 0 or network.netbits == 0:
            return True
        cmp = self.addr.compare(network.addr)
        if cmp == EQUALS:
            return False
        if cmp == BEFORE:
            alpha = self.duplicate().next()
            bravo = network
        else:
            alpha = network.duplicate().next()
            bravo = self
        if not alpha.is_valid():
            return False
        if alpha.addr.compare(bravo.addr) == EQUALS:
            return True
        return False
