import builtins
from unittest.mock import patch

import pytest

import aikido_zen
from aikido_zen import protect
from aikido_zen.background_process.ipc import IPCClient
from aikido_zen.helpers.token import get_token_from_env


def test_protect_with_django(monkeypatch, caplog):
    protect()

    assert "starting" in caplog.text
    IPCClient.reset()
    assert IPCClient.get() == None


def test_protect_sets_token():
    aikido_zen.protect(token="MY_TOKEN_1")
    assert get_token_from_env().token == "MY_TOKEN_1"


def test_protect_does_not_start_without_gil(monkeypatch):
    monkeypatch.setattr("aikido_zen.gil_not_enabled", lambda: True)

    with patch("aikido_zen.check_socket_access") as check_socket_access, patch(
        "aikido_zen.start_background_process"
    ) as start_background_process:
        protect()

    check_socket_access.assert_not_called()
    start_background_process.assert_not_called()


def test_protect_registers_the_odoo_source(monkeypatch):
    imported_modules = []
    original_import = builtins.__import__

    def track_import(name, *args, **kwargs):
        imported_modules.append(name)
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("aikido_zen.aikido_disabled_flag_active", lambda: False)
    monkeypatch.setattr("aikido_zen.python_version_not_supported", lambda: False)
    monkeypatch.setattr("aikido_zen.gil_not_enabled", lambda: False)
    monkeypatch.setattr("aikido_zen.test_uds_file_access", lambda: True)
    monkeypatch.setattr("aikido_zen.check_gevent", lambda: False)
    monkeypatch.setattr(builtins, "__import__", track_import)

    protect(mode="daemon_disabled")

    assert "aikido_zen.sources.odoo" in imported_modules
