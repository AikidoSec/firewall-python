import pytest
from .extract_ip_array_from_results import extract_ip_array_from_results


def test_extract_ip_array_from_results_with_valid_ips():
    dns_results = [
        ("example.com", "A", 3600, "IN", ["192.168.1.1"]),
        ("example.org", "A", 3600, "IN", ["10.0.0.1"]),
        ("example.net", "A", 3600, "IN", ["172.16.0.1"]),
    ]
    expected_ips = ["192.168.1.1", "10.0.0.1", "172.16.0.1"]
    result = extract_ip_array_from_results(dns_results)
    assert result == expected_ips


def test_extract_ip_array_from_results_with_none_ip():
    dns_results = [
        ("example.com", "A", 3600, "IN", [None]),
        ("example.org", "A", 3600, "IN", ["10.0.0.1"]),
        ("example.net", "A", 3600, "IN", [None]),
    ]
    expected_ips = ["10.0.0.1"]
    result = extract_ip_array_from_results(dns_results)
    assert result == expected_ips


def test_extract_ip_array_from_results_with_empty_results():
    dns_results = []
    expected_ips = []
    result = extract_ip_array_from_results(dns_results)
    assert result == expected_ips


def test_extract_ip_array_from_results_with_empty_ip():
    dns_results = [
        ("example.org", "A", 3600, "IN", [None]),
        ("example.net", "A", 3600, "IN", ["192.168.1.1"]),
    ]
    expected_ips = ["192.168.1.1"]
    result = extract_ip_array_from_results(dns_results)
    assert result == expected_ips


def test_extract_ip_array_from_results_with_mixed_results():
    dns_results = [
        ("example.com", "A", 3600, "IN", ["192.168.1.1"]),
        ("example.org", "A", 3600, "IN", [None]),
        ("example.edu", "A", 3600, "IN", ["10.0.0.1"]),
    ]
    expected_ips = ["192.168.1.1", "10.0.0.1"]
    result = extract_ip_array_from_results(dns_results)
    assert result == expected_ips
