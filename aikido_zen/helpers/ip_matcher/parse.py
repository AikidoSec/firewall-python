"""
Based on https://github.com/demskie/netparser
MIT License - Copyright (c) 2019 alex
"""

import math
import re


def network(s):
    s = s.strip()
    parts = s.split("/")
    if len(parts) == 0 or len(parts) > 2:
        return None
    is_ipv4 = looks_like_ipv4(s)
    if is_ipv4 is None:
        return None
    cidr = 32 if is_ipv4 else 128
    if len(parts) == 2:
        x = parse_int_range(parts[1], 0, cidr)
        if x is None:
            return None
        cidr = x
    bytes_data = v4_addr_to_bytes(parts[0]) if is_ipv4 else v6_addr_to_bytes(parts[0])
    if bytes_data is None:
        return None
    return {"bytes": bytes_data, "cidr": cidr}


def looks_like_ipv4(s):
    for c in s:
        if c == ".":
            return True
        if c == ":":
            return False
    return None


def parse_int_range(old, min_val, max_val):
    s = ""
    for i in range(len(old)):
        if not old[i].isdigit():
            break
        s += old[i]
    if not s:
        return None
    x = int(s)
    if min_val <= x <= max_val:
        return x
    return None


def v4_addr_to_bytes(old):
    bytes_data = [0] * 4
    parts = old.split(".")
    if len(parts) == 4:
        for i in range(4):
            try:
                x = int(parts[i])
            except ValueError:
                return None
            if 0 <= x <= 255:
                bytes_data[i] = x
            else:
                return None
        return bytes_data
    return None


def v6_addr_to_bytes(s):
    bytes_data = [0] * 16
    if not s:
        return None
    s = remove_brackets(s)
    if s == "::":
        return bytes_data
    halves = s.split("::")
    if len(halves) == 0 or len(halves) > 2:
        return None
    left_byte_index = parse_left_half(bytes_data, halves[0])
    if left_byte_index is None:
        return None
    if len(halves) == 2:
        right_byte_index = parse_right_half(bytes_data, halves[1], left_byte_index)
        if right_byte_index is None:
            return None
    return bytes_data


def remove_brackets(s):
    if s.startswith("["):
        for i in range(len(s) - 1, -1, -1):
            if s[i] == "]":
                return s[1:i]
    return s


def parse_hextet(s):
    s = s.strip()
    if len(s) < 1 or len(s) > 4:
        return float("nan")
    val = 0
    for i in range(len(s)):
        try:
            x = int(s[i], 16)
        except ValueError:
            return float("nan")
        val += x * (2 ** (4 * (len(s) - i - 1)))
    return val


def parse_left_half(bytes_data, left_half):
    left_byte_index = 0
    if left_half != "":
        left_parts = left_half.split(":")
        for i in range(len(left_parts)):
            if left_byte_index >= 16:
                return None
            ipv4_parts = left_parts[i].split(".")
            if len(ipv4_parts) == 0:
                return None
            if len(ipv4_parts) != 4:
                x = parse_hextet(left_parts[i])
                if isinstance(x, float) and math.isnan(x):
                    return None
                if x < 0 or x > 65535:
                    return None
                bytes_data[left_byte_index] = x // 256
                bytes_data[left_byte_index + 1] = x % 256
                left_byte_index += 2
            else:
                for j in range(len(ipv4_parts)):
                    try:
                        x = int(ipv4_parts[j])
                    except ValueError:
                        return None
                    if x < 0 or x > 255:
                        return None
                    bytes_data[left_byte_index] = x
                    left_byte_index += 1
    return left_byte_index


def parse_right_half(bytes_data, right_half, left_byte_index):
    right_byte_index = 15
    if right_half != "":
        right_parts = right_half.split(":")
        for i in range(len(right_parts) - 1, -1, -1):
            if not right_parts[i].strip():
                return None
            if left_byte_index > right_byte_index:
                return None
            ipv4_parts = right_parts[i].split(".")
            if len(ipv4_parts) == 0:
                return None
            if len(ipv4_parts) != 4:
                if i == len(right_parts) - 1:
                    right_parts[i] = remove_port_info(right_parts[i])
                x = parse_hextet(right_parts[i])
                if isinstance(x, float) and math.isnan(x):
                    return None
                if x < 0 or x > 65535:
                    return None
                bytes_data[right_byte_index] = x % 256
                bytes_data[right_byte_index - 1] = x // 256
                right_byte_index -= 2
            else:
                for j in range(len(ipv4_parts) - 1, -1, -1):
                    try:
                        x = int(ipv4_parts[j])
                    except ValueError:
                        return None
                    if x < 0 or x > 255:
                        return None
                    bytes_data[right_byte_index] = x
                    right_byte_index -= 1
    return right_byte_index


def remove_port_info(s):
    return re.sub(r"(#|p|\.).*", "", s).strip()
