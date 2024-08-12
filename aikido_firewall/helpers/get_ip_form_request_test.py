import pytest
from .get_ip_from_request import (
    get_ip_from_request,
    is_ip,
    get_client_ip_from_x_forwarded_for,
)


# Test `get_ip_from_request` function :
def test_get_ip_from_request():
    # Test case 1: Valid X_FORWARDED_FOR header with valid IP
    headers = {"X_FORWARDED_FOR": "192.168.1.1, 10.0.0.1"}
    assert get_ip_from_request(None, headers) == "192.168.1.1"

    # Test case 2: Valid X_FORWARDED_FOR header with invalid IPs
    headers = {"X_FORWARDED_FOR": "256.256.256.256, 192.168.1.1"}
    assert (
        get_ip_from_request(None, headers) == "192.168.1.1"
    )  # Should return the valid IP

    # Test case 3: Valid remote address
    headers = {}
    assert get_ip_from_request("10.0.0.1", headers) == "10.0.0.1"

    # Test case 4: Valid remote address with invalid X_FORWARDED_FOR
    headers = {"X_FORWARDED_FOR": "abc.def.ghi.jkl, 256.256.256.256"}
    assert (
        get_ip_from_request("10.0.0.1", headers) == "10.0.0.1"
    )  # Should return the remote address

    # Test case 5: Both X_FORWARDED_FOR and remote address are invalid
    headers = {"X_FORWARDED_FOR": "abc.def.ghi.jkl, 256.256.256.256"}
    assert get_ip_from_request(None, headers) is None  # Should return None

    # Test case 6: Empty headers and remote address
    headers = {}
    assert get_ip_from_request(None, headers) is None  # Should return None


#  Test `is_ip` function :
def test_valid_ipv4():
    assert is_ip("192.168.1.1")  # Valid IPv4
    assert is_ip("255.255.255.255")  # Valid IPv4
    assert is_ip("0.0.0.0")  # Valid IPv4


def test_invalid_ipv4():
    assert not is_ip("256.256.256.256")  # Invalid IPv4
    assert not is_ip("192.168.1")  # Invalid IPv4
    assert not is_ip("abc.def.ghi.jkl")  # Invalid IPv4


def test_valid_ipv6():
    assert is_ip("::1")  # Valid IPv6 (loopback)
    assert is_ip("2001:0db8:85a3:0000:0000:8a2e:0370:7334")  # Valid IPv6


def test_invalid_ipv6():
    assert not is_ip("2001:db8:85a3::8a2e:370:7334:12345")  # Invalid IPv6
    assert not is_ip("::g")  # Invalid IPv6


#  Test `get_client_ip_from_x_forwarded_for` function :
def test_get_client_ip_from_x_forwarded_for():
    # Test cases with valid IPs
    assert get_client_ip_from_x_forwarded_for("192.168.1.1") == "192.168.1.1"
    assert get_client_ip_from_x_forwarded_for("192.168.1.1, 10.0.0.1") == "192.168.1.1"
    assert get_client_ip_from_x_forwarded_for("10.0.0.1, 192.168.1.1") == "10.0.0.1"
    assert (
        get_client_ip_from_x_forwarded_for("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
        == "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    )
    assert (
        get_client_ip_from_x_forwarded_for(
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334, 192.168.1.1"
        )
        == "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    )

    # Test cases with mixed valid and invalid IPs
    assert (
        get_client_ip_from_x_forwarded_for("256.256.256.256, 192.168.1.1")
        == "192.168.1.1"
    )  # Invalid IPv4 ignored
    assert (
        get_client_ip_from_x_forwarded_for("192.168.1.1, abc.def.ghi.jkl")
        == "192.168.1.1"
    )  # Invalid IPv4 ignored
    assert (
        get_client_ip_from_x_forwarded_for(
            "::1, 2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        )
        == "::1"
    )  # Valid IPv6 preferred

    # Test cases with only invalid IPs
    assert (
        get_client_ip_from_x_forwarded_for("abc.def.ghi.jkl, 256.256.256.256") is None
    )  # All invalid
    assert get_client_ip_from_x_forwarded_for("") is None  # Empty string
