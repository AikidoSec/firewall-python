import aikido_zen.background_process as background_process


def test_python314_forkserver_default_uses_fork_context(monkeypatch, mocker):
    monkeypatch.setattr(background_process.sys, "version_info", (3, 14))
    mocker.patch.object(
        background_process.multiprocessing,
        "get_start_method",
        return_value="forkserver",
    )
    fork_context = mocker.patch.object(
        background_process.multiprocessing,
        "get_context",
    ).return_value

    assert background_process.get_process_factory() == fork_context.Process
    background_process.multiprocessing.get_context.assert_called_once_with("fork")


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
