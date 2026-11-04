import pytest
import socket
from aikido_zen.helpers.get_hostname import get_hostname


@pytest.fixture(autouse=True)
def reset_cached_hostname():
    get_hostname.cache_clear()


def test_get_hostname_success(monkeypatch):
    monkeypatch.setattr(socket, "gethostname", lambda: "mocked_hostname")

    assert get_hostname() == "mocked_hostname"


def test_get_hostname_failure(monkeypatch):
    monkeypatch.setattr(
        socket,
        "gethostname",
        lambda: (_ for _ in ()).throw(OSError("Mocked exception")),
    )

    assert get_hostname() == ""


def test_get_hostname_is_read_once(monkeypatch):
    calls = []
    monkeypatch.setattr(
        socket, "gethostname", lambda: calls.append(None) or "mocked_hostname"
    )

    assert get_hostname() == get_hostname()
    assert len(calls) == 1
