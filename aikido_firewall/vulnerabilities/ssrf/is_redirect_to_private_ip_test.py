import pytest
from unittest.mock import MagicMock, patch
from .is_redirect_to_private_ip import is_redirect_to_private_ip
from urllib.parse import urlparse, urlunparse


# Helper function to create URL objects
def create_url(href):
    return urlparse(href)


def test_is_redirect_to_private_ip_success():
    url = create_url("http://192.168.0.1/")  # Private IP
    context = MagicMock()
    context.outgoing_req_redirects = [
        {
            "source": create_url("http://example.com"),
            "destination": create_url("http://192.168.0.1/"),
        },
    ]
    context.parsed_userinput = {}
    context.body = {"field": ["http://example.com"]}
    with patch("aikido_firewall.context.get_current_context", return_value=context):
        result = is_redirect_to_private_ip(url, context)
        assert result == {
            "pathToPayload": ".field.[0]",
            "payload": "http://example.com",
            "source": "body",
        }


def test_is_redirect_to_private_ip_no_redirects():
    url = create_url("http://192.168.0.1/")  # Private IP
    context = MagicMock()
    context.outgoing_req_redirects = []

    result = is_redirect_to_private_ip(url, context)
    assert result is None


def test_is_redirect_to_private_ip_not_private_ip():
    url = create_url("https://example.com/")  # Not a private IP
    context = MagicMock()
    context.outgoing_req_redirects = [
        {
            "source": create_url("http://example.com"),
            "destination": create_url("http://hackers.com"),
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
    url = create_url("http://192.168.0.1/")  # Private IP
    context = MagicMock()
    context.outgoing_req_redirects = [
        {
            "source": create_url("http://example.com"),
            "destination": create_url("http://notfound.com"),
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
    url = create_url("http://192.168.0.1/")  # Private IP
    context = MagicMock()
    context.outgoing_req_redirects = [
        {
            "source": create_url("http://example.com"),
            "destination": create_url("http://hackers.com"),
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
