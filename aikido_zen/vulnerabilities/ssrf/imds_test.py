import pytest
from .imds import is_imds_ip_address, resolves_to_imds_ip


def test_returns_true_for_imds_ip_addresses():
    assert is_imds_ip_address("169.254.169.254") is True
    assert is_imds_ip_address("fd00:ec2::254") is True


def test_returns_false_for_non_imds_ip_addresses():
    assert is_imds_ip_address("1.2.3.4") is False
    assert is_imds_ip_address("example.com") is False


# --- Tests ---
def test_trusted_hostname_returns_false():
    """Test that trusted hostnames always return False."""
    assert resolves_to_imds_ip(["1.1.1.1"], "metadata.google.internal") is False


def test_aws_imds_ipv4_present_returns_ip():
    """Test that an AWS IMDS IPv4 address is returned if present."""
    assert (
        resolves_to_imds_ip(["169.254.169.254", "8.8.8.8"], "example.com")
        == "169.254.169.254"
    )


def test_aws_imds_ipv6_present_returns_ip():
    """Test that an AWS IMDS IPv6 address is returned if present."""
    assert (
        resolves_to_imds_ip(["fd00:ec2::254", "2001:db8::1"], "example.com")
        == "fd00:ec2::254"
    )


def test_alibaba_imds_ip_present_returns_ip():
    """Test that an Alibaba IMDS IP address is returned if present."""
    assert (
        resolves_to_imds_ip(["100.100.100.200", "8.8.8.8"], "example.com")
        == "100.100.100.200"
    )


def test_no_imds_ip_present_returns_false():
    """Test that False is returned if no IMDS IP is present."""
    assert resolves_to_imds_ip(["8.8.8.8", "1.1.1.1"], "example.com") is False


def test_empty_ip_list_returns_false():
    """Test that False is returned if the IP list is empty."""
    assert resolves_to_imds_ip([], "example.com") is False


def test_mixed_imds_and_normal_ips():
    """Test that the first IMDS IP in the list is returned."""
    assert (
        resolves_to_imds_ip(
            ["8.8.8.8", "169.254.169.254", "100.100.100.200"], "example.com"
        )
        == "169.254.169.254"
    )
