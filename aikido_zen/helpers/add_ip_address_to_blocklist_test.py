import pytest
from .add_ip_address_to_blocklist import add_ip_address_to_blocklist
from .blocklist import BlockList


def test_valid_ips():
    blocklist = BlockList()

    assert add_ip_address_to_blocklist("1.2.3.4", blocklist) is True
    assert blocklist.is_blocked("1.2.3.4") is True

    assert add_ip_address_to_blocklist("fd00:ec2::254", blocklist) is True
    assert blocklist.is_blocked("fd00:ec2::254") is True

    assert add_ip_address_to_blocklist("192.168.2.1/24", blocklist) is True
    assert blocklist.is_blocked("192.168.2.1") is True
    assert blocklist.is_blocked("192.168.2.240") is True

    assert add_ip_address_to_blocklist("fd00:124::1/64", blocklist) is True
    assert blocklist.is_blocked("fd00:124::1") is True
    assert blocklist.is_blocked("fd00:124::f") is True
    assert blocklist.is_blocked("fd00:124::ff13") is True

    assert add_ip_address_to_blocklist("fd00:f123::1/128", blocklist) is True
    assert blocklist.is_blocked("fd00:f123::1") is True

    assert blocklist.is_blocked("2.3.4.5") is False
    assert blocklist.is_blocked("fd00:125::ff13") is False
    assert blocklist.is_blocked("fd00:f123::2") is False


def test_invalid_ips():
    blocklist = BlockList()

    assert add_ip_address_to_blocklist("192.168.2.2.1/24", blocklist) is False
    assert add_ip_address_to_blocklist("test", blocklist) is False
    assert add_ip_address_to_blocklist("", blocklist) is False
    assert add_ip_address_to_blocklist("192.168.2.1/64", blocklist) is False
    assert add_ip_address_to_blocklist("fd00:124::1/129", blocklist) is False
    assert add_ip_address_to_blocklist("fd00:124::1/0", blocklist) is False
    assert add_ip_address_to_blocklist("fd00:124::1/test", blocklist) is False
