import pytest
from unittest.mock import MagicMock
from .is_redirect_to_private_ip import is_redirect_to_private_ip

"""
def test_is_redirect_to_private_ip_success():
    url = {"hostname": "192.168.0.1", "href": "http://192.168.0.1   "}  # Private IP
    context = MagicMock()
    context.outgoing_req_redirects = [
        {
            "source": {
                "href": "http://example.com",
                "hostname": "example.com",
                "port": "80",
            },
            "destination": {"href": "http://hackers.com"},
        },
    ]

    # Mock the necessary functions
    with MagicMock() as mock_contains_private_ip_address, \
         MagicMock() as mock_get_redirect_origin, \
         MagicMock() as mock_find_hostname_in_context:
        
        mock_contains_private_ip_address.return_value = True
        mock_get_redirect_origin.return_value = MagicMock(hostname="example.com", port=80)
        mock_find_hostname_in_context.return_value = True

        # Replace the actual functions with mocks
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr('aikido_firewall.vulnerabilities.ssrf.contains_private_ip_address', mock_contains_private_ip_address)
            mp.setattr('aikido_firewall.vulnerabilities.ssrf.get_redirect_origin', mock_get_redirect_origin)
            mp.setattr('aikido_firewall.vulnerabilities.ssrf.find_hostname_in_context', mock_find_hostname_in_context)

            result = is_redirect_to_private_ip(url, context)
            assert result is True
"""


def test_is_redirect_to_private_ip_no_redirects():
    url = {"hostname": "192.168.0.1", "href": "http://192.168.0.1/"}  # Private IP
    context = MagicMock()
    context.outgoing_req_redirects = []

    result = is_redirect_to_private_ip(url, context)
    assert result is None


def test_is_redirect_to_private_ip_not_private_ip():
    url = {
        "hostname": "example.com",
        "href": "https://example.com/",
    }  # Not a private IP
    context = MagicMock()
    context.outgoing_req_redirects = [
        {
            "source": {
                "href": "http://example.com",
                "hostname": "example.com",
                "port": "80",
            },
            "destination": {"href": "http://hackers.com"},
        },
    ]

    with MagicMock() as mock_contains_private_ip_address:
        mock_contains_private_ip_address.return_value = False
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "aikido_firewall.vulnerabilities.ssrf.contains_private_ip_address",
                mock_contains_private_ip_address,
            )

            result = is_redirect_to_private_ip(url, context)
            assert result is None


def test_is_redirect_to_private_ip_redirect_origin_not_found():
    url = {"hostname": "192.168.0.1", "href": "http://192.168.0.1/"}  # Private IP
    context = MagicMock()
    context.outgoing_req_redirects = [
        {
            "source": {
                "href": "http://example.com",
                "hostname": "example.com",
                "port": "80",
            },
            "destination": {"href": "http://notfound.com"},
        },
    ]

    with MagicMock() as mock_contains_private_ip_address, MagicMock() as mock_get_redirect_origin:

        mock_contains_private_ip_address.return_value = True
        mock_get_redirect_origin.return_value = None

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "aikido_firewall.vulnerabilities.ssrf.contains_private_ip_address",
                mock_contains_private_ip_address,
            )
            mp.setattr(
                "aikido_firewall.vulnerabilities.ssrf.get_redirect_origin",
                mock_get_redirect_origin,
            )

            result = is_redirect_to_private_ip(url, context)
            assert result is None


def test_is_redirect_to_private_ip_hostname_not_found_in_context():
    url = {"hostname": "192.168.0.1", "href": "http://192.168.0.1/"}  # Private IP
    context = MagicMock()
    context.outgoing_req_redirects = [
        {
            "source": {
                "href": "http://example.com",
                "hostname": "example.com",
                "port": "80",
            },
            "destination": {"href": "http://hackers.com"},
        },
    ]

    with MagicMock() as mock_contains_private_ip_address, MagicMock() as mock_get_redirect_origin, MagicMock() as mock_find_hostname_in_context:

        mock_contains_private_ip_address.return_value = True
        mock_get_redirect_origin.return_value = MagicMock(
            hostname="example.com", port=80
        )
        mock_find_hostname_in_context.return_value = False

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "aikido_firewall.vulnerabilities.ssrf.contains_private_ip_address",
                mock_contains_private_ip_address,
            )
            mp.setattr(
                "aikido_firewall.vulnerabilities.ssrf.get_redirect_origin",
                mock_get_redirect_origin,
            )
            mp.setattr(
                "aikido_firewall.vulnerabilities.ssrf.find_hostname_in_context",
                mock_find_hostname_in_context,
            )

            result = is_redirect_to_private_ip(url, context)
            assert result is None
