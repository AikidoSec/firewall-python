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


def test_protect_rejects_invalid_mode():
    with pytest.raises(ValueError, match=r"Invalid mode .*protect\(token=\.\.\.\)"):
        aikido_zen.protect("AIK_RUNTIME_some-token-string")


@pytest.mark.parametrize("mode", ["daemon", "daemon_only", "daemon_disabled"])
def test_protect_accepts_valid_modes(mode):
    aikido_zen.protect(mode=mode)
