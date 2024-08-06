import pytest
from .is_private_ip import is_private_ip


# Test cases for is_private_ip
def test_private_ipv4_addresses():
    assert is_private_ip("192.168.1.1") is True
    assert is_private_ip("10.0.0.1") is True
    assert is_private_ip("172.16.0.1") is True
    assert is_private_ip("127.0.0.1") is True
    assert is_private_ip("169.254.1.1") is True


def test_public_ipv4_addresses():
    assert is_private_ip("8.8.8.8") is False
    assert is_private_ip("172.15.0.1") is False


def test_private_ipv6_addresses():
    assert is_private_ip("::1") is True  # Loopback address
    assert is_private_ip("fc00::1") is True  # Unique local address
    assert is_private_ip("fe80::1") is True  # Link-local address


def test_public_ipv6_addresses():
    assert is_private_ip("2001:db8::1") is False  # Documentation address
    assert is_private_ip("::ffff:8.8.8.8") is False  # IPv4-mapped address


def test_invalid_addresses():
    assert is_private_ip("invalid-ip") is False
    assert is_private_ip("") is False
    assert is_private_ip("256.256.256.256") is False  # Invalid IPv4
    assert is_private_ip("::g") is False  # Invalid IPv6
