from types import SimpleNamespace

from aikido_zen.helpers.python_version_not_supported import (
    python_version_not_supported,
)


def test_python_3_14_is_supported(monkeypatch):
    monkeypatch.setattr(
        "aikido_zen.helpers.python_version_not_supported.sys.version_info",
        SimpleNamespace(major=3, minor=14),
    )

    assert python_version_not_supported() is False


def test_python_3_15_is_not_supported(monkeypatch, caplog):
    monkeypatch.setattr(
        "aikido_zen.helpers.python_version_not_supported.sys.version_info",
        SimpleNamespace(major=3, minor=15),
    )

    assert python_version_not_supported() is True
    assert "doesn't support versions above Python 3.14" in caplog.text


def test_non_python_3_version_is_not_supported(monkeypatch, caplog):
    monkeypatch.setattr(
        "aikido_zen.helpers.python_version_not_supported.sys.version_info",
        SimpleNamespace(major=4, minor=0),
    )

    assert python_version_not_supported() is True
    assert "only supports Python 3" in caplog.text
