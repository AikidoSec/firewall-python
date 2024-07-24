import pytest
from aikido_firewall import protect
from aikido_firewall.agent import get_ipc


def test_protect_with_django(monkeypatch, caplog):
    monkeypatch.setitem(
        globals(), "aikido_firewall.sources.django", "dummy_django_module"
    )
    monkeypatch.setitem(
        globals(), "aikido_firewall.sinks.pymysql", "dummy_pymysql_module"
    )
    monkeypatch.setenv("AIKIDO_SECRET_KEY", "mock_key")

    protect(module="django")

    assert "Aikido python firewall started" in caplog.text
    assert get_ipc() != None
    get_ipc().agent_proc.kill()
