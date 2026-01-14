import pytest
import math
from .network import Network


def test_empty_network_cidr():
    result = Network().cidr()
    assert math.isnan(result)


def test_set_cidr_zero_invalid():
    assert not Network().set_cidr(0).is_valid()


def test_valid_network_is_valid():
    assert Network("192.168.2.1/24").is_valid()


def test_set_invalid_cidr_invalidates_network():
    assert not Network("192.168.2.1/24").set_cidr(-1).is_valid()


def test_compare_empty_networks():
    assert Network().compare(Network()) is None


def test_compare_valid_and_empty_networks():
    assert Network("192.168.2.1/24").compare(Network()) is None


def test_empty_network_does_not_contain_empty_network():
    assert not Network().contains(Network())


def test_valid_network_does_not_contain_empty_network():
    assert not Network("192.168.2.1/24").contains(Network())


def test_network_contains_subnetwork():
    assert Network("192.168.2.1/24").contains(Network("192.168.2.1/32"))


if __name__ == "__main__":
    pytest.main([__file__])
