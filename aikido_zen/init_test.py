import pytest

import aikido_zen
from aikido_zen import protect
from aikido_zen.background_process import get_comms, reset_comms
from aikido_zen.helpers.token import get_token_from_env


def test_protect_with_django(monkeypatch, caplog):
    protect()

    assert "starting" in caplog.text
    reset_comms()
    assert get_comms() == None


def test_protect_sets_token():
    aikido_zen.protect(token="MY_TOKEN_1")
    assert get_token_from_env().token == "MY_TOKEN_1"
