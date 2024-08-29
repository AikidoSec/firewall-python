import pytest
from aikido_firewall import protect
from aikido_firewall.background_process import get_comms, reset_comms


def test_protect_with_django(monkeypatch, caplog):
    monkeypatch.setitem(
        globals(), "aikido_firewall.sources.django", "dummy_django_module"
    )
    monkeypatch.setitem(
        globals(), "aikido_firewall.sinks.pymysql", "dummy_pymysql_module"
    )

    protect()

    assert "starting" in caplog.text
    assert get_comms() != None
    reset_comms()
    assert get_comms() == None
