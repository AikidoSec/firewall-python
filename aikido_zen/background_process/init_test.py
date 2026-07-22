import aikido_zen.background_process as background_process


def test_stale_socket_removed_by_another_worker(monkeypatch, mocker):
    process = mocker.patch("aikido_zen.background_process.Process")
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
