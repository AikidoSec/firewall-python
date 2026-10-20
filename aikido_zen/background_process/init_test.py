import json
import multiprocessing
import subprocess
import sys

import pytest

import aikido_zen.background_process as background_process
from aikido_zen.background_process.aikido_background_process import (
    AikidoBackgroundProcess,
)
from aikido_zen.helpers.get_agent_session_id import (
    get_agent_session_id,
    set_agent_session_id,
)
from .ipc_test import reset_ipc_after_test


@pytest.mark.parametrize("version", [(3, 8), (3, 13), (3, 14)])
def test_configured_forkserver_uses_fork_context(monkeypatch, mocker, version):
    monkeypatch.setattr(sys, "version_info", version)
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


def test_unset_forkserver_default_uses_fork_context(mocker):
    get_start_method = mocker.patch.object(
        background_process.multiprocessing,
        "get_start_method",
        return_value=None,
    )
    mocker.patch.object(
        background_process.multiprocessing,
        "get_all_start_methods",
        return_value=["forkserver", "spawn", "fork"],
    )
    fork_context = mocker.patch.object(
        background_process.multiprocessing,
        "get_context",
    ).return_value

    assert background_process.get_process_factory() == fork_context.Process
    get_start_method.assert_called_once_with(allow_none=True)
    background_process.multiprocessing.get_context.assert_called_once_with("fork")


@pytest.mark.parametrize("start_method", ["spawn", "fork"])
def test_configured_method_is_preserved(mocker, start_method):
    get_start_method = mocker.patch.object(
        background_process.multiprocessing,
        "get_start_method",
        return_value=start_method,
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


@pytest.mark.parametrize("system", ["Darwin", "Windows"])
@pytest.mark.parametrize("version", [(3, 8), (3, 13), (3, 14)])
def test_unset_spawn_default_is_preserved(monkeypatch, mocker, system, version):
    monkeypatch.setattr(sys, "version_info", version)
    monkeypatch.setattr(background_process.platform, "system", lambda: system)
    mocker.patch.object(
        background_process.multiprocessing, "get_start_method", return_value=None
    )
    mocker.patch.object(
        background_process.multiprocessing,
        "get_all_start_methods",
        return_value=(
            ["spawn"] if system == "Windows" else ["spawn", "fork", "forkserver"]
        ),
    )
    get_context = mocker.patch.object(background_process.multiprocessing, "get_context")

    assert (
        background_process.get_process_factory()
        == background_process.multiprocessing.Process
    )
    get_context.assert_not_called()


def test_unset_fork_default_is_preserved(mocker):
    mocker.patch.object(
        background_process.multiprocessing, "get_start_method", return_value=None
    )
    mocker.patch.object(
        background_process.multiprocessing,
        "get_all_start_methods",
        return_value=["fork", "spawn", "forkserver"],
    )
    get_context = mocker.patch.object(background_process.multiprocessing, "get_context")

    assert (
        background_process.get_process_factory()
        == background_process.multiprocessing.Process
    )
    get_context.assert_not_called()


@pytest.mark.parametrize("system", ["Darwin", "Linux"])
@pytest.mark.parametrize("start_method", [None, "spawn", "forkserver"])
def test_uwsgi_uses_fork_context(monkeypatch, mocker, system, start_method):
    monkeypatch.setattr(background_process.platform, "system", lambda: system)
    monkeypatch.setitem(sys.modules, "uwsgi", mocker.Mock())
    mocker.patch.object(
        background_process.multiprocessing,
        "get_start_method",
        return_value=start_method,
    )
    fork_context = mocker.patch.object(
        background_process.multiprocessing, "get_context"
    ).return_value

    assert background_process.get_process_factory() == fork_context.Process
    background_process.multiprocessing.get_context.assert_called_once_with("fork")


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


def test_socket_name_is_stable_and_separates_tokens(monkeypatch):
    monkeypatch.setenv("AIKIDO_TOKEN", "AIK_RUNTIME_TEST")
    current = background_process.get_uds_filename()

    assert current == background_process.get_uds_filename()
    monkeypatch.setenv("AIKIDO_TOKEN", "AIK_RUNTIME_OTHER")
    assert current != background_process.get_uds_filename()


@pytest.mark.parametrize("method", multiprocessing.get_all_start_methods())
def test_socket_name_is_shared_by_workers_and_unique_to_each_run(
    monkeypatch, tmp_path, method
):
    monkeypatch.setenv("AIKIDO_TOKEN", "AIK_RUNTIME_TEST")
    script = tmp_path / "worker_socket_names.py"
    script.write_text(
        """
import json
import multiprocessing
import sys

def worker(pipe):
    from aikido_zen.background_process import get_uds_filename
    pipe.send(get_uds_filename())
    pipe.close()

if __name__ == "__main__":
    context = multiprocessing.get_context(sys.argv[1])
    readers, processes = [], []
    for _ in range(2):
        reader, writer = context.Pipe(duplex=False)
        process = context.Process(target=worker, args=(writer,))
        process.start()
        writer.close()
        readers.append(reader)
        processes.append(process)
    for process in processes:
        process.join(10)
        assert process.exitcode == 0
    from aikido_zen.background_process import get_uds_filename
    names = [get_uds_filename()] + [reader.recv() for reader in readers]
    print(json.dumps(names))
""",
        encoding="utf-8",
    )
    runs = [
        json.loads(
            subprocess.check_output(
                [sys.executable, str(script), method], text=True, timeout=25
            )
        )
        for _ in range(2)
    ]

    assert all(len(set(names)) == 1 for names in runs)
    assert runs[0][0] != runs[1][0]


def test_startup_does_not_reuse_a_legacy_socket(monkeypatch, mocker):
    factory = mocker.patch.object(
        background_process, "get_process_factory"
    ).return_value
    active = mocker.patch.object(
        background_process, "background_process_already_active", return_value=True
    )
    monkeypatch.setenv("AIKIDO_TOKEN", "AIK_RUNTIME_TEST")
    monkeypatch.setenv("AIKIDO_TMP_DIR", "/tmp")
    monkeypatch.setattr(background_process.platform, "system", lambda: "Linux")
    legacy = f"/tmp/aikido_python_{background_process.hash_aikido_token()}.sock"
    monkeypatch.setattr(
        background_process.os.path, "exists", lambda path: path == legacy
    )

    background_process.start_background_process()

    active.assert_not_called()
    assert factory.call_args.kwargs["args"][0] != legacy
    factory.return_value.start.assert_called_once_with()


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
        background_process, "background_process_already_active", lambda _ipc: False
    )
    monkeypatch.setattr(
        background_process.os,
        "remove",
        mocker.Mock(side_effect=FileNotFoundError),
    )

    background_process.start_background_process()

    process.return_value.start.assert_called_once_with()


def test_started_process_receives_the_current_session_id(monkeypatch, mocker):
    process = mocker.patch(
        "aikido_zen.background_process.get_process_factory"
    ).return_value
    monkeypatch.setenv("AIKIDO_TOKEN", "AIK_RUNTIME_TEST")
    monkeypatch.setattr(background_process.platform, "system", lambda: "Linux")
    monkeypatch.setattr(
        background_process, "get_uds_filename", lambda: "/tmp/aikido-session.sock"
    )
    monkeypatch.setattr(background_process.os.path, "exists", lambda _path: False)

    background_process.start_background_process()

    assert process.call_args.kwargs["args"][2] == get_agent_session_id()


def test_background_process_adopts_the_parent_session_id(monkeypatch):
    def listener(*_args, **_kwargs):
        raise OSError("address in use")

    original = get_agent_session_id()
    monkeypatch.setattr(
        "aikido_zen.background_process.aikido_background_process.con.Listener",
        listener,
    )
    try:
        with pytest.raises(SystemExit):
            AikidoBackgroundProcess("/tmp/zen-session.sock", b"key", "parent-session")
        assert get_agent_session_id() == "parent-session"
    finally:
        set_agent_session_id(original)
