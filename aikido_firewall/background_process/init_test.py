import pytest
from aikido_firewall.background_process import (
    IPC,
    start_background_process,
    get_comms,
    IPC_ADDRESS,
    reset_comms,
)


def test_ipc_init():
    address = ("localhost", 9898)
    key = "secret_key"
    ipc = IPC(address, key)

    assert ipc.address == address
    assert ipc.key == key


def test_start_background_process(monkeypatch):
    reset_comms()
    assert get_comms() == None
    start_background_process()

    assert get_comms() != None
    assert get_comms().address == IPC_ADDRESS

    reset_comms()
    assert get_comms() == None


def test_send_data_to_bg_process_exception(monkeypatch, caplog):
    def mock_client(address, authkey):
        raise Exception("Connection Error")

    monkeypatch.setitem(globals(), "Client", mock_client)
    monkeypatch.setitem(globals(), "logger", caplog)

    ipc = IPC(("localhost", 9898), "mock_key")
    ipc.send_data_to_bg_process("ACTION", "Test Object")


def test_send_data_to_bg_process_successful(monkeypatch, caplog, mocker):
    ipc = IPC(("localhost"), "mock_key")
    mock_client = mocker.MagicMock()
    monkeypatch.setattr("multiprocessing.connection.Client", mock_client)

    # Call the send_data_to_bg_process function
    ipc.send_data_to_bg_process("ACTION", {"key": "value"})
