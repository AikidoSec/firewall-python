import subprocess
import sys

import aikido_zen.background_process as background_process
from .comms_test import reset_comms_after_test


def test_configured_forkserver_uses_fork_context(mocker):
    get_start_method = mocker.patch.object(
        background_process.multiprocessing,
        "get_start_method",
        return_value="forkserver",
    )
    fork_context = mocker.patch.object(
        background_process.multiprocessing,
        "get_context",
    ).return_value

    assert background_process.get_process_factory() == fork_context.Process
    get_start_method.assert_called_once_with(allow_none=True)
    background_process.multiprocessing.get_context.assert_called_once_with("fork")


def test_unset_default_uses_fork_context(mocker):
    get_start_method = mocker.patch.object(
        background_process.multiprocessing,
        "get_start_method",
        return_value=None,
    )
    fork_context = mocker.patch.object(
        background_process.multiprocessing,
        "get_context",
    ).return_value

    assert background_process.get_process_factory() == fork_context.Process
    get_start_method.assert_called_once_with(allow_none=True)
    background_process.multiprocessing.get_context.assert_called_once_with("fork")


def test_configured_spawn_uses_configured_context(mocker):
    get_start_method = mocker.patch.object(
        background_process.multiprocessing,
        "get_start_method",
        return_value="spawn",
    )
    get_context = mocker.patch.object(
        background_process.multiprocessing,
        "get_context",
    )

    assert (
        background_process.get_process_factory()
        == background_process.multiprocessing.Process
    )
    get_start_method.assert_called_once_with(allow_none=True)
    get_context.assert_not_called()


def test_windows_unset_default_uses_configured_context(monkeypatch, mocker):
    monkeypatch.setattr(background_process.platform, "system", lambda: "Windows")
    mocker.patch.object(
        background_process.multiprocessing, "get_start_method", return_value=None
    )
    get_context = mocker.patch.object(background_process.multiprocessing, "get_context")

    assert (
        background_process.get_process_factory()
        == background_process.multiprocessing.Process
    )
    get_context.assert_not_called()


def test_get_process_factory_does_not_set_global_start_method():
    script = """
import multiprocessing

assert multiprocessing.get_start_method(allow_none=True) is None

from aikido_zen.background_process import get_process_factory

assert multiprocessing.get_start_method(allow_none=True) is None
get_process_factory()
assert multiprocessing.get_start_method(allow_none=True) is None
"""

    subprocess.run([sys.executable, "-c", script], check=True)


def test_stale_socket_removed_by_another_worker(monkeypatch, mocker):
    process = mocker.patch(
        "aikido_zen.background_process.get_process_factory"
    ).return_value
    monkeypatch.setenv("AIKIDO_TOKEN", "AIK_RUNTIME_TEST")
    monkeypatch.setattr(background_process.platform, "system", lambda: "Linux")
    monkeypatch.setattr(
        background_process, "get_uds_filename", lambda: "/tmp/aikido.sock"
    )
    monkeypatch.setattr(background_process.os.path, "exists", lambda _path: True)
    monkeypatch.setattr(
        background_process, "background_process_already_active", lambda _comms: False
    )
    monkeypatch.setattr(
        background_process.os,
        "remove",
        mocker.Mock(side_effect=FileNotFoundError),
    )

    background_process.start_background_process()

    process.return_value.start.assert_called_once_with()
