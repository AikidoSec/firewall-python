import pytest
import socket
from aikido_zen.helpers.get_machine_ip import get_ip


@pytest.fixture(autouse=True)
def reset_cached_ip_address():
    get_ip.cache_clear()


def test_get_ip_success(monkeypatch):
    # Mock the socket.gethostname to return a specific hostname
    monkeypatch.setattr(socket, "gethostname", lambda: "mocked_hostname")
    # Mock the socket.gethostbyname to return a specific IP address
    monkeypatch.setattr(socket, "gethostbyname", lambda hostname: "192.168.1.1")

    assert get_ip() == "192.168.1.1"


def test_get_ip_failure(monkeypatch):
    # Mock the socket.gethostname to return a specific hostname
    monkeypatch.setattr(socket, "gethostname", lambda: "mocked_hostname")
    # Mock the socket.gethostbyname to raise an exception
    monkeypatch.setattr(
        socket,
        "gethostbyname",
        lambda hostname: (_ for _ in ()).throw(Exception("Mocked exception")),
    )

    assert get_ip() == "x.x.x.x"


def test_get_ip_is_resolved_once(monkeypatch):
    calls = []
    monkeypatch.setattr(socket, "gethostname", lambda: "mocked_hostname")
    monkeypatch.setattr(
        socket,
        "gethostbyname",
        lambda hostname: calls.append(hostname) or "192.168.1.1",
    )

    assert get_ip() == get_ip()
    assert len(calls) == 1


def test_get_ip_resolves_a_failure_once(monkeypatch):
    calls = []
    monkeypatch.setattr(socket, "gethostname", lambda: "mocked_hostname")
    monkeypatch.setattr(
        socket,
        "gethostbyname",
        lambda hostname: calls.append(hostname)
        or (_ for _ in ()).throw(Exception("Mocked exception")),
    )

    assert get_ip() == get_ip() == "x.x.x.x"
    assert len(calls) == 1
