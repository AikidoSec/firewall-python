from aikido_zen.helpers.gil_not_enabled import gil_not_enabled


def test_gil_enabled(monkeypatch):
    monkeypatch.setattr(
        "aikido_zen.helpers.gil_not_enabled.sys._is_gil_enabled",
        lambda: True,
        raising=False,
    )

    assert gil_not_enabled() is False


def test_gil_disabled(monkeypatch, caplog):
    monkeypatch.setattr(
        "aikido_zen.helpers.gil_not_enabled.sys._is_gil_enabled",
        lambda: False,
        raising=False,
    )

    assert gil_not_enabled() is True
    assert "does not support running Python with the GIL disabled" in caplog.text


def test_python_without_runtime_gil_check(monkeypatch):
    monkeypatch.delattr(
        "aikido_zen.helpers.gil_not_enabled.sys._is_gil_enabled", raising=False
    )

    assert gil_not_enabled() is False
