import pytest
from unittest.mock import MagicMock, patch
from .is_redirect_to_private_ip import is_redirect_to_private_ip
from urllib.parse import urlparse, urlunparse


# Helper function to create URL objects
def create_url(href):
    return urlparse(href)


def test_is_redirect_to_private_ip_success():
    context = MagicMock()
    context.outgoing_req_redirects = [
        {
            "source": create_url("http://example.com"),
            "destination": create_url("http://192.168.0.1/"),
        },
    ]
    context.parsed_userinput = {}
    context.body = {"field": ["http://example.com"]}
    with patch("aikido_zen.context.get_current_context", return_value=context):
        result = is_redirect_to_private_ip("192.168.0.1", context, 80)
        assert result == {
            "pathToPayload": ".field.[0]",
            "payload": "http://example.com",
            "source": "body",
        }


def test_is_redirect_to_private_ip_no_redirects():
    context = MagicMock()
    context.outgoing_req_redirects = []

    result = is_redirect_to_private_ip("192.168.0.1", context, 80)
    assert result is None


def test_is_redirect_to_private_ip_not_private_ip():
    context = MagicMock()
    context.outgoing_req_redirects = [
        {
            "source": create_url("http://example.com"),
            "destination": create_url("http://hackers.com"),
        },
    ]

    result = is_redirect_to_private_ip("example.com", context, 443)
    assert result is None


def test_is_redirect_to_private_ip_redirect_origin_not_found():
    context = MagicMock()
    context.outgoing_req_redirects = [
        {
            "source": create_url("http://example.com"),
            "destination": create_url("http://notfound.com"),
        },
    ]

    with MagicMock() as mock_get_redirect_origin:
        mock_get_redirect_origin.return_value = None

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "aikido_zen.vulnerabilities.ssrf.get_redirect_origin",
                mock_get_redirect_origin,
            )

            result = is_redirect_to_private_ip("192.168.0.1", context, 80)
            assert result is None


def test_is_redirect_to_private_ip_hostname_not_found_in_context():
    context = MagicMock()
    context.outgoing_req_redirects = [
        {
            "source": create_url("http://example.com"),
            "destination": create_url("http://hackers.com"),
        },
    ]

    with MagicMock() as mock_get_redirect_origin, MagicMock() as mock_find_hostname_in_context:
        mock_get_redirect_origin.return_value = MagicMock(
            hostname="example.com", port=80
        )
        mock_find_hostname_in_context.return_value = False

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "aikido_zen.vulnerabilities.ssrf.get_redirect_origin",
                mock_get_redirect_origin,
            )
            mp.setattr(
                "aikido_zen.vulnerabilities.ssrf.find_hostname_in_context",
                mock_find_hostname_in_context,
            )

            result = is_redirect_to_private_ip("192.168.0.1", context, 80)
            assert result is None
