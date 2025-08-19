from aikido_zen.helpers.ip_matcher.network import Network
from aikido_zen.helpers.ip_matcher.shared import summarize_sorted_networks


def test_summarize_sorted_networks_empty():
    result = summarize_sorted_networks([])
    assert result == []


def test_summarize_sorted_networks_single():
    networks = [Network("192.168.1.0/24")]
    result = summarize_sorted_networks(networks)
    assert len(result) == 1
    assert result[0].addr.bytes() == [192, 168, 1, 0]
    assert result[0].cidr() == 24


def test_summarize_sorted_networks_no_merge():
    networks = [Network("192.168.1.0/24"), Network("192.168.3.0/24")]
    result = summarize_sorted_networks(networks)
    assert len(result) == 2
    assert result[0].addr.bytes() == [192, 168, 1, 0]
    assert result[0].cidr() == 24
    assert result[1].addr.bytes() == [192, 168, 3, 0]
    assert result[1].cidr() == 24
