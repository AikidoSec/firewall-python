import pytest
import math
from .network import Network
from .sort import native_sort, binary_search_for_insertion_index


def test_native_sort_empty_list():
    networks = []
    result = native_sort(networks)
    assert result == []


def test_native_sort_single_network():
    networks = [Network("192.168.1.1/24")]
    result = native_sort(networks)
    assert len(result) == 1
    assert result[0].addr.bytes() == [192, 168, 1, 1]
    assert result[0].cidr() == 24


def test_native_sort_different_byte_lengths():
    networks = [
        Network("::1/64"),  # IPv6
        Network("192.168.1.1/24"),  # IPv4
    ]
    result = native_sort(networks)
    assert len(result) == 2
    assert len(result[0].addr.bytes()) == 4  # IPv4
    assert len(result[1].addr.bytes()) == 16  # IPv6


def test_native_sort_same_byte_length_different_bytes():
    networks = [
        Network("192.168.2.1/24"),
        Network("192.168.1.1/24"),
    ]
    result = native_sort(networks)
    assert len(result) == 2
    assert result[0].addr.bytes() == [192, 168, 1, 1]
    assert result[1].addr.bytes() == [192, 168, 2, 1]


def test_native_sort_same_bytes_different_cidrs():
    networks = [
        Network("192.168.1.1/24"),
        Network("192.168.1.1/16"),
    ]
    result = native_sort(networks)
    assert len(result) == 2
    assert result[0].cidr() == 16
    assert result[1].cidr() == 24


def test_native_sort_invalid_networks():
    invalid_net = Network().destroy()
    valid_net = Network("192.168.1.1/24")
    networks = [invalid_net, valid_net]
    result = native_sort(networks)
    assert len(result) == 2
    assert not result[0].is_valid()
    assert result[1].is_valid()


def test_native_sort_already_sorted():
    networks = [
        Network("192.168.1.1/16"),
        Network("192.168.1.1/24"),
        Network("192.168.2.1/24"),
    ]
    original_bytes = [net.addr.bytes() for net in networks]
    original_cidrs = [net.cidr() for net in networks]
    result = native_sort(networks)
    assert len(result) == 3
    for i in range(3):
        assert result[i].addr.bytes() == original_bytes[i]
        assert result[i].cidr() == original_cidrs[i]


def test_native_sort_reverse_order():
    networks = [
        Network("192.168.2.1/24"),
        Network("192.168.1.1/24"),
        Network("192.168.1.1/16"),
    ]
    result = native_sort(networks)
    assert len(result) == 3
    assert result[0].addr.bytes() == [192, 168, 1, 1]
    assert result[0].cidr() == 16
    assert result[1].addr.bytes() == [192, 168, 1, 1]
    assert result[1].cidr() == 24
    assert result[2].addr.bytes() == [192, 168, 2, 1]
    assert result[2].cidr() == 24


def test_binary_search_empty_list():
    network = Network("192.168.1.1/24")
    assert binary_search_for_insertion_index(network, []) == 0


def test_binary_search_insert_at_beginning():
    networks = [
        Network("192.168.2.1/24"),
        Network("192.168.3.1/24"),
    ]
    new_network = Network("192.168.1.1/24")
    assert binary_search_for_insertion_index(new_network, networks) == 0


def test_binary_search_insert_at_end():
    networks = [
        Network("192.168.1.1/24"),
        Network("192.168.2.1/24"),
    ]
    new_network = Network("192.168.3.1/24")
    assert binary_search_for_insertion_index(new_network, networks) == 2


def test_binary_search_insert_in_middle():
    networks = [
        Network("192.168.1.1/24"),
        Network("192.168.3.1/24"),
    ]
    new_network = Network("192.168.2.1/24")
    assert binary_search_for_insertion_index(new_network, networks) == 1


def test_binary_search_mixed_ipv4_ipv6():
    networks = [
        Network("192.168.1.1/24"),
        Network("::1/64"),
    ]
    new_network1 = Network("192.168.0.1/24")
    assert binary_search_for_insertion_index(new_network1, networks) == 0
    new_network2 = Network("192.168.2.1/24")
    assert binary_search_for_insertion_index(new_network2, networks) == 1
    new_network3 = Network("::0/64")
    assert binary_search_for_insertion_index(new_network3, networks) == 1
    new_network4 = Network("::2/64")
    assert binary_search_for_insertion_index(new_network4, networks) == 2


def test_binary_search_mixed_multiple_networks():
    networks = [
        Network("192.168.1.1/24"),
        Network("192.168.2.1/24"),
        Network("::1/64"),
        Network("::2/64"),
    ]
    new_network1 = Network("192.168.0.1/24")
    assert binary_search_for_insertion_index(new_network1, networks) == 0
    new_network2 = Network("192.168.1.2/24")
    assert binary_search_for_insertion_index(new_network2, networks) == 1
    new_network3 = Network("192.168.3.1/24")
    assert binary_search_for_insertion_index(new_network3, networks) == 2
    new_network4 = Network("::0/64")
    assert binary_search_for_insertion_index(new_network4, networks) == 2
    new_network5 = Network("::1.5/64")
    assert binary_search_for_insertion_index(new_network5, networks) == 3
    new_network6 = Network("::3/64")
    assert binary_search_for_insertion_index(new_network6, networks) == 4
