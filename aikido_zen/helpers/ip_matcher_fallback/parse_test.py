import pytest
from .parse import network


def test_ipv4_valid_cidr():
    result = network("192.168.2.1/24")
    expected = {"bytes": [192, 168, 2, 1], "cidr": 24}
    assert result == expected


def test_ipv4_invalid_cidr():
    result = network("192.168.2.1/abcde")
    assert result is None


def test_ipv4_additional_text():
    result = network("192.168.2.1/24/test")
    assert result is None


def test_ipv6_valid():
    result = network("::1")
    expected = {"bytes": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], "cidr": 128}
    assert result == expected
