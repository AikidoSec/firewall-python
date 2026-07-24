from unittest.mock import patch

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


def test_protect_does_not_start_without_gil(monkeypatch):
    monkeypatch.setattr("aikido_zen.gil_not_enabled", lambda: True)

    with patch("aikido_zen.test_uds_file_access") as test_uds_file_access, patch(
        "aikido_zen.start_background_process"
    ) as start_background_process:
        protect()

    test_uds_file_access.assert_not_called()
    start_background_process.assert_not_called()
