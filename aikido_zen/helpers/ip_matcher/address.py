"""
Based on https://github.com/demskie/netparser
MIT License - Copyright (c) 2019 alex
"""

from aikido_zen.helpers.ip_matcher import parse

# Constants
BEFORE = -1
EQUALS = 0
AFTER = 1


class Address:
    def __init__(self, address=None):
        self.arr = []
        if address:
            net = parse.network(address)
            if net:
                self.arr = net["bytes"]

    def bytes(self):
        return self.arr if self.arr else []

    def set_bytes(self, bytes_data):
        if len(bytes_data) == 4 or len(bytes_data) == 16:
            self.arr = bytes_data
        else:
            self.arr = []
        return self

    def destroy(self):
        if self.is_valid():
            self.arr = []
        return self

    def is_valid(self):
        return len(self.arr) > 0

    def is_ipv4(self):
        return len(self.arr) == 4

    def is_ipv6(self):
        return len(self.arr) == 16

    def duplicate(self):
        return Address().set_bytes(self.arr.copy())

    def equals(self, address):
        return self.compare(address) == EQUALS

    def compare(self, address):
        if not self.is_valid() or not address.is_valid():
            return None
        if self == address:
            return EQUALS
        if len(self.arr) < len(address.arr):
            return BEFORE
        if len(self.arr) > len(address.arr):
            return AFTER

        for i in range(len(self.arr)):
            if self.arr[i] < address.arr[i]:
                return BEFORE
            if self.arr[i] > address.arr[i]:
                return AFTER

        return EQUALS

    def apply_subnet_mask(self, cidr):
        if not self.is_valid():
            return self
        mask_bits = len(self.arr) * 8 - cidr
        for i in range(len(self.arr) - 1, -1, -1):
            mask = max(0, min(mask_bits, 8))
            if mask == 0:
                return self
            self.arr[i] &= ~((1 << mask) - 1)
            mask_bits -= 8
        return self

    def is_base_address(self, cidr):
        if not self.is_valid() or cidr < 0 or cidr > len(self.arr) * 8:
            return False
        if cidr == len(self.arr) * 8:
            return True
        mask_bits = len(self.arr) * 8 - cidr
        for i in range(len(self.arr) - 1, -1, -1):
            mask = max(0, min(mask_bits, 8))
            if mask == 0:
                return True
            if self.arr[i] != (self.arr[i] & ~((1 << mask) - 1)):
                return False
            mask_bits -= 8
        return True

    def increase(self, cidr):
        if self.is_valid():
            self.offset_address(cidr, True)
        else:
            self.destroy()
        return self

    def offset_address(self, cidr, forwards, throw_errors=False):
        target_byte = (cidr - 1) // 8
        if self.is_valid() and 0 <= target_byte < len(self.arr):
            increment = 2 ** (8 - (cidr - target_byte * 8))
            self.arr[target_byte] += increment * (1 if forwards else -1)
            if target_byte >= 0:
                if self.arr[target_byte] < 0:
                    self.arr[target_byte] = 256 + (self.arr[target_byte] % 256)
                    self.offset_address(target_byte * 8, forwards, throw_errors)
                elif self.arr[target_byte] > 255:
                    self.arr[target_byte] %= 256
                    self.offset_address(target_byte * 8, forwards, throw_errors)
            else:
                self.destroy()
        else:
            self.destroy()
