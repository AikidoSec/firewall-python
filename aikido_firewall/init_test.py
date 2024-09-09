import pytest
from aikido_firewall import protect
from aikido_firewall.background_process import get_comms, reset_comms


def test_protect_with_django(monkeypatch, caplog):

    protect()

    assert "starting" in caplog.text
    reset_comms()
    assert get_comms() == None
