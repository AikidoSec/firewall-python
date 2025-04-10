import os
import pytest

from aikido_zen.vulnerabilities.ssrf.is_request_to_itself import is_request_to_itself


@pytest.fixture(autouse=True)
def clear_environment():
    # Clear the environment variable before each test
    os.environ.pop("AIKIDO_TRUST_PROXY", None)


def test_returns_false_if_server_url_is_empty():
    assert not is_request_to_itself("", "aikido.dev", 80)


def test_returns_false_if_server_url_is_invalid():
    assert not is_request_to_itself("http://", "aikido.dev", 80)


def test_returns_false_if_port_is_different():
    assert not is_request_to_itself("http://aikido.dev:4000", "aikido.dev", 80)
    assert not is_request_to_itself("https://aikido.dev:4000", "aikido.dev", 443)


def test_returns_false_if_hostname_is_different():
    assert not is_request_to_itself("http://aikido.dev", "google.com", 80)
    assert not is_request_to_itself("http://aikido.dev:4000", "google.com", 4000)
    assert not is_request_to_itself("https://aikido.dev", "google.com", 443)
    assert not is_request_to_itself("https://aikido.dev:4000", "google.com", 443)


def test_returns_true_if_server_does_request_to_itself():
    assert is_request_to_itself("https://aikido.dev", "aikido.dev", 443)
    assert is_request_to_itself("http://aikido.dev:4000", "aikido.dev", 4000)
    assert is_request_to_itself("http://aikido.dev", "aikido.dev", 80)
    assert is_request_to_itself("https://aikido.dev:4000", "aikido.dev", 4000)


def test_returns_true_for_special_case_http_to_https():
    assert is_request_to_itself("http://aikido.dev", "aikido.dev", 443)
    assert is_request_to_itself("https://aikido.dev", "aikido.dev", 80)


def test_returns_false_if_trust_proxy_is_false(monkeypatch):
    monkeypatch.setenv("AIKIDO_TRUST_PROXY", "false")
    assert not is_request_to_itself("https://aikido.dev", "aikido.dev", 443)
    assert not is_request_to_itself("http://aikido.dev", "aikido.dev", 80)


def test_returns_false_if_server_url_is_null():
    assert not is_request_to_itself(None, "aikido.dev", 80)
    assert not is_request_to_itself(None, "aikido.dev", 443)


def test_returns_false_if_hostname_is_null():
    assert not is_request_to_itself("http://aikido.dev:4000", None, 80)
    assert not is_request_to_itself("https://aikido.dev:4000", None, 443)


def test_returns_false_if_both_are_null():
    assert not is_request_to_itself(None, None, 80)
    assert not is_request_to_itself(None, None, 443)
