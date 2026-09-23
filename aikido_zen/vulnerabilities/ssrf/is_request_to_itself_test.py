import os
import pytest

from aikido_zen.vulnerabilities.ssrf.is_request_to_itself import is_request_to_itself


@pytest.fixture(autouse=True)
def clear_environment():
    os.environ.pop("AIKIDO_TRUSTED_HOSTNAMES", None)
    yield
    os.environ.pop("AIKIDO_TRUSTED_HOSTNAMES", None)


def test_returns_false_if_no_trusted_hostnames_configured():
    assert not is_request_to_itself("aikido.dev")
    assert not is_request_to_itself("localhost")


def test_returns_false_if_hostname_not_in_trusted_list(monkeypatch):
    monkeypatch.setenv("AIKIDO_TRUSTED_HOSTNAMES", "myapp.com,api.myapp.com")
    assert not is_request_to_itself("aikido.dev")
    assert not is_request_to_itself("google.com")


def test_returns_true_if_hostname_in_trusted_list(monkeypatch):
    monkeypatch.setenv("AIKIDO_TRUSTED_HOSTNAMES", "myapp.com,api.myapp.com")
    assert is_request_to_itself("myapp.com")
    assert is_request_to_itself("api.myapp.com")


def test_returns_true_for_single_trusted_hostname(monkeypatch):
    monkeypatch.setenv("AIKIDO_TRUSTED_HOSTNAMES", "aikido.dev")
    assert is_request_to_itself("aikido.dev")


def test_strips_whitespace_from_trusted_hostnames(monkeypatch):
    monkeypatch.setenv("AIKIDO_TRUSTED_HOSTNAMES", "  myapp.com ,  api.myapp.com  ")
    assert is_request_to_itself("myapp.com")
    assert is_request_to_itself("api.myapp.com")


def test_returns_false_if_hostname_is_none():
    assert not is_request_to_itself(None)


def test_returns_false_if_hostname_is_empty():
    assert not is_request_to_itself("")


def test_returns_false_if_hostname_is_not_a_string():
    assert not is_request_to_itself(123)
    assert not is_request_to_itself(["myapp.com"])
