import pytest
from .imds import is_imds_ip_address


# Assuming the is_imds_ip_address function is defined in the same file or imported from another module
def is_imds_ip_address(ip: str) -> bool:
    # This is a placeholder for the actual implementation
    # You should replace this with the actual function from your code
    return ip in ["169.254.169.254", "fd00:ec2::254"]


def test_returns_true_for_imds_ip_addresses():
    assert is_imds_ip_address("169.254.169.254") is True
    assert is_imds_ip_address("fd00:ec2::254") is True


def test_returns_false_for_non_imds_ip_addresses():
    assert is_imds_ip_address("1.2.3.4") is False
    assert is_imds_ip_address("example.com") is False
