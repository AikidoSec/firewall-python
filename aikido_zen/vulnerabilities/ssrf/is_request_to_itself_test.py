import pytest

from aikido_zen.vulnerabilities.ssrf.is_request_to_itself import is_request_to_itself


@pytest.mark.parametrize(
    "server_url, hostname, port, expected",
    [
        ("", "aikido.dev", 80, False),
        ("http://", "aikido.dev", 80, False),
        ("http://aikido.dev:4000", "aikido.dev", 80, False),
        ("https://aikido.dev:4000", "aikido.dev", 443, False),
        ("http://aikido.dev", "google.com", 80, False),
        ("http://aikido.dev:4000", "google.com", 4000, False),
        ("https://aikido.dev", "google.com", 443, False),
        ("https://aikido.dev:4000", "google.com", 443, False),
        ("https://aikido.dev", "aikido.dev", 443, True),
        ("http://aikido.dev:4000", "aikido.dev", 4000, True),
        ("http://aikido.dev", "aikido.dev", 80, True),
        ("https://aikido.dev:4000", "aikido.dev", 4000, True),
        ("http://aikido.dev", "aikido.dev", 443, True),
        ("https://aikido.dev", "aikido.dev", 80, True),
        (None, "aikido.dev", 80, False),
        (None, "aikido.dev", 443, False),
        ("http://aikido.dev:4000", None, 80, False),
        ("https://aikido.dev:4000", None, 443, False),
        (None, None, 80, False),
        (None, None, 443, False),
    ],
)
def test_request_to_itself(server_url, hostname, port, expected):
    assert is_request_to_itself(server_url, hostname, port, True) is expected


@pytest.mark.parametrize("trusted", [False, None])
def test_untrusted_request_cannot_bypass_ssrf(trusted):
    assert not is_request_to_itself("https://aikido.dev", "aikido.dev", 443, trusted)
    assert not is_request_to_itself("http://aikido.dev", "aikido.dev", 80, trusted)
