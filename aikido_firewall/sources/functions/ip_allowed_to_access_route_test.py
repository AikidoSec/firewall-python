import pytest
from unittest.mock import MagicMock
from aikido_firewall.helpers.is_localhost_ip import is_localhost_ip
from .ip_allowed_to_access_route import ip_allowed_to_access_route


class SampleContext:
    def __init__(self, remote_address):
        self.remote_address = remote_address


class SampleReporter:
    def __init__(self, conf):
        self.conf = conf


@pytest.fixture
def reporter_with_endpoints():
    class SampleConf:
        def get_endpoints(*args):
            return [
                {"allowedIPAddresses": ["192.168.1.1", "10.0.0.1"]},
                {"allowedIPAddresses": []},
                {"allowedIPAddresses": "not_a_list"},  # Invalid type
                {"allowedIPAddresses": ["127.0.0.1"]},  # Localhost
            ]

    return SampleReporter(SampleConf)


def test_localhost_ip_access(reporter_with_endpoints):
    context = SampleContext("127.0.0.1")
    assert ip_allowed_to_access_route(context, reporter_with_endpoints) is True


def test_localhost_ip_access_ipv6(reporter_with_endpoints):
    context = SampleContext("::1")
    assert ip_allowed_to_access_route(context, reporter_with_endpoints) is True


def test_ip_in_allowed_list(reporter_with_endpoints):
    context = SampleContext("192.168.1.1")
    assert ip_allowed_to_access_route(context, reporter_with_endpoints) is False


def test_ip_not_in_allowed_list(reporter_with_endpoints):
    context = SampleContext("192.168.1.2")
    assert ip_allowed_to_access_route(context, reporter_with_endpoints) is False


def test_empty_allowed_list(reporter_with_endpoints):
    context = SampleContext("192.168.1.1")
    assert ip_allowed_to_access_route(context, reporter_with_endpoints) is False


def test_invalid_allowed_ip_type(reporter_with_endpoints):
    context = SampleContext("192.168.1.1")
    assert ip_allowed_to_access_route(context, reporter_with_endpoints) is False


def test_remote_address_none(reporter_with_endpoints):
    context = SampleContext(None)
    assert ip_allowed_to_access_route(context, reporter_with_endpoints) is False


def test_multiple_endpoints_with_various_configs(reporter_with_endpoints):
    context = SampleContext("10.0.0.1")
    assert ip_allowed_to_access_route(context, reporter_with_endpoints) is False

    context = SampleContext("127.0.0.1")
    assert ip_allowed_to_access_route(context, reporter_with_endpoints) is True

    context = SampleContext("192.168.1.2")
    assert ip_allowed_to_access_route(context, reporter_with_endpoints) is False

    context = SampleContext("::ffff:127.0.0.1")
    assert ip_allowed_to_access_route(context, reporter_with_endpoints) is True


def test_no_endpoints(reporter_with_endpoints):
    reporter_with_endpoints.conf.get_endpoints = lambda context: []
    context = SampleContext("192.168.1.1")
    assert (
        ip_allowed_to_access_route(context, reporter_with_endpoints) is True
    )  # No restrictions
