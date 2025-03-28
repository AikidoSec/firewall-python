import pytest
from .iplist import IPList, get_ip_address_type


def test_get_ip_address_type():
    # Valid IPv4 addresses
    assert get_ip_address_type("192.168.1.1") == "ipv4"
    assert get_ip_address_type("255.255.255.255") == "ipv4"
    assert get_ip_address_type("0.0.0.0") == "ipv4"

    # Valid IPv6 addresses
    assert get_ip_address_type("::1") == "ipv6"
    assert get_ip_address_type("2001:0db8:85a3:0000:0000:8a2e:0370:7334") == "ipv6"
    assert get_ip_address_type("::") == "ipv6"

    # Invalid IP addresses
    assert get_ip_address_type("invalid_ip") is None
    assert get_ip_address_type("") is None
    assert get_ip_address_type("192.168.1.256") is None  # Invalid octet
    assert (
        get_ip_address_type("2001:0db8:85a3:0000:0000:8a2e:0370:7334:1234") is None
    )  # Too many segments


def test_blocklist_add_address():
    blocklist = IPList()
    assert blocklist.matches("192.168.1.1") is False
    blocklist.add_address("192.168.1.1", "ipv4")
    assert blocklist.matches("192.168.1.1") is True

    # Test adding the same address again
    blocklist.add_address("192.168.1.1", "ipv4")
    assert len(blocklist.blocked_addresses) == 1  # Should still be one entry


def test_blocklist_add_subnet():
    blocklist = IPList()
    assert blocklist.matches("10.0.0.1") is False
    blocklist.add_subnet("10.0.0.0", 8, "ipv4")
    assert blocklist.matches("10.0.0.1") is True
    assert blocklist.matches("10.1.1.1") is True
    assert blocklist.matches("192.168.1.1") is False


def test_blocklist_multiple_addresses_and_subnets():
    blocklist = IPList()
    blocklist.add_address("192.168.1.1", "ipv4")
    blocklist.add_subnet("10.0.0.0", 8, "ipv4")

    assert blocklist.matches("192.168.1.1") is True
    assert blocklist.matches("10.0.0.1") is True
    assert blocklist.matches("10.1.1.1") is True
    assert blocklist.matches("172.16.0.1") is False


def test_blocklist_invalid_ip():
    blocklist = IPList()
    blocklist.add_address("192.168.1.1", "ipv4")
    assert blocklist.matches("invalid_ip") is False


def test_blocklist_subnet_edge_cases():
    blocklist = IPList()
    blocklist.add_subnet("192.168.1.0", 24, "ipv4")

    assert blocklist.matches("192.168.1.255") is True  # Last address in the subnet
    assert blocklist.matches("192.168.1.0") is True  # First address in the subnet
    assert blocklist.matches("192.168.2.1") is False  # Outside the subnet
    assert blocklist.matches("192.168.1.128") is True  # Middle of the subnet


def test_blocklist_ipv6():
    blocklist = IPList()
    blocklist.add_address("2001:0db8:85a3:0000:0000:8a2e:0370:7334", "ipv6")
    assert blocklist.matches("2001:0db8:85a3:0000:0000:8a2e:0370:7334") is True
    assert blocklist.matches("::1") is False  # Not in the blocklist

    blocklist.add_subnet("2001:0db8::", 32, "ipv6")
    assert blocklist.matches("2001:0db8:abcd:0012:0000:0000:0000:0001") is True
    assert blocklist.matches("2001:0db9::") is False  # Outside the subnet


def test_blocklist_overlapping_subnets():
    blocklist = IPList()
    blocklist.add_subnet(
        "192.168.1.0", 24, "ipv4"
    )  # Covers 192.168.1.0 to 192.168.1.255
    blocklist.add_subnet(
        "192.168.1.128", 25, "ipv4"
    )  # Covers 192.168.1.128 to 192.168.1.255

    assert blocklist.matches("192.168.1.130") is True  # Inside both subnets
    assert blocklist.matches("192.168.1.0") is True  # Inside first subnet
    assert (
        blocklist.matches("192.168.1.127") is True
    )  # Inside first subnet, outside second
    assert blocklist.matches("192.168.1.255") is True  # Last address in both subnets
    assert blocklist.matches("192.168.2.1") is False  # Outside both subnets


def test_blocklist_mixed_address_types():
    blocklist = IPList()
    blocklist.add_address("192.168.1.1", "ipv4")
    blocklist.add_address("2001:0db8:85a3:0000:0000:8a2e:0370:7334", "ipv6")

    assert blocklist.matches("192.168.1.1") is True
    assert blocklist.matches("2001:0db8:85a3:0000:0000:8a2e:0370:7334") is True
    assert blocklist.matches("192.168.1.2") is False  # Different IPv4
    assert (
        blocklist.matches("2001:0db8:85a3:0000:0000:8a2e:0370:7335") is False
    )  # Different IPv6


def test_blocklist_subnet_with_single_ip():
    blocklist = IPList()
    blocklist.add_subnet("192.168.1.1", 32, "ipv4")  # Single IP subnet

    assert blocklist.matches("192.168.1.1") is True
    assert blocklist.matches("192.168.1.2") is False  # Outside the subnet


# Tests add function
def test_valid_ips():
    blocklist = IPList()

    blocklist.add("1.2.3.4")
    assert blocklist.matches("1.2.3.4") is True

    blocklist.add("fd00:ec2::254")
    assert blocklist.matches("fd00:ec2::254") is True

    blocklist.add("192.168.2.1/24")
    assert blocklist.matches("192.168.2.1") is True
    assert blocklist.matches("192.168.2.240") is True

    blocklist.add("fd00:124::1/64")
    assert blocklist.matches("fd00:124::1") is True
    assert blocklist.matches("fd00:124::f") is True
    assert blocklist.matches("fd00:124::ff13") is True

    blocklist.add("fd00:f123::1/128")
    assert blocklist.matches("fd00:f123::1") is True

    assert blocklist.matches("2.3.4.5") is False
    assert blocklist.matches("fd00:125::ff13") is False
    assert blocklist.matches("fd00:f123::2") is False


def test_invalid_ips():
    blocklist = IPList()

    blocklist.add("192.168.2.2.1/24")
    assert blocklist.matches("192.168.2.2.1") is False

    blocklist.add("test")
    assert blocklist.matches("test") is False

    blocklist.add("")
    assert blocklist.matches("") is False

    blocklist.add("fd00:124::1/test")
    assert blocklist.matches("fd00:124::1") is False
