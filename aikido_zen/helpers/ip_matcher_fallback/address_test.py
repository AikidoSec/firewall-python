import pytest
from .address import Address


def test_is_ipv4():
    assert Address("1.2.3.5").is_ipv4() == True
    assert Address("::1").is_ipv4() == False


def test_is_ipv6():
    assert Address("::1").is_ipv6() == True


def test_compare():
    assert Address("1.2.3.4").compare(Address("1.2.3.5")) == -1
    assert Address("1.2.3.4").compare(Address("1.2.3.4")) == 0
    assert Address("1.2.3.4").compare(Address("1.2.3.4").duplicate()) == 0

    # edge cases
    assert Address().compare(Address()) is None
    assert Address("1.2.3.4").compare(Address()) is None


def test_bytes_method():
    assert Address("1.2.3.4").bytes() == [1, 2, 3, 4]
    assert Address().bytes() == []


def test_set_bytes_method():
    assert Address("1.2.3.4").set_bytes([3]).bytes() == []


def test_equals_method():
    assert Address("1.2.3.4").equals(Address("1.2.3.4")) == True
    assert Address("1.2.3.4").equals(Address("1.2.3.5")) == False


def test_apply_subnet_mask():
    assert Address().apply_subnet_mask(0) is not None


def test_increase_method():
    assert Address().increase(0).bytes() == []
    assert Address().bytes() == []


def test_self_comparison():
    a = Address("3.4.5.6")
    assert a.compare(a) == 0
