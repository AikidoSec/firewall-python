import pytest
from aikido_firewall import protect
from aikido_firewall.background_process import get_comms


def test_protect_with_django(monkeypatch, caplog):
    monkeypatch.setitem(
        globals(), "aikido_firewall.sources.django", "dummy_django_module"
    )
    monkeypatch.setitem(
        globals(), "aikido_firewall.sinks.pymysql", "dummy_pymysql_module"
    )

    protect(module="django")

    assert "Aikido python firewall started" in caplog.text
    assert get_comms() != None
    get_comms().background_process.kill()
