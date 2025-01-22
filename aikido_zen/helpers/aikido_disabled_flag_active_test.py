import pytest
from .aikido_disabled_flag_active import aikido_disabled_flag_active


def test_aikido_disabled_flag_does_not_exist(monkeypatch):
    monkeypatch.setenv("AIKIDO_DISABLE", None)
    assert aikido_disabled_flag_active() == False


def test_aikido_disabled_flag_exists_but_invalid(monkeypatch):
    monkeypatch.setenv("AIKIDO_DISABLE", "token")
    assert aikido_disabled_flag_active() == False


def test_aikido_disabled_flag_exists_and_off(monkeypatch):
    monkeypatch.setenv("AIKIDO_DISABLE", "0")
    assert aikido_disabled_flag_active() == False

    monkeypatch.setenv("AIKIDO_DISABLE", "false")
    assert aikido_disabled_flag_active() == False

    monkeypatch.setenv("AIKIDO_DISABLE", "False")
    assert aikido_disabled_flag_active() == False


def test_aikido_disabled_flag_exists_and_on(monkeypatch):
    monkeypatch.setenv("AIKIDO_DISABLE", "1")
    assert aikido_disabled_flag_active() == True

    monkeypatch.setenv("AIKIDO_DISABLE", "True")
    assert aikido_disabled_flag_active() == True

    monkeypatch.setenv("AIKIDO_DISABLE", "TRUE")
    assert aikido_disabled_flag_active() == True

    monkeypatch.setenv("AIKIDO_DISABLE", "true")
    assert aikido_disabled_flag_active() == True
