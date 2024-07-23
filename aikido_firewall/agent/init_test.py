import pytest
from aikido_firewall.agent import IPC, start_ipc, get_ipc, IPC_ADDRESS


def test_ipc_init():
    address = ("localhost", 9898)
    key = "secret_key"
    ipc = IPC(address, key)

    assert ipc.address == address
    assert ipc.key == b"secret_key"  # Ensure key is encoded as bytes
    assert ipc.agent_proc is None


def test_start_ipc_missing_secret_key(mocker):
    mocker.patch("os.environ", {})

    with pytest.raises(EnvironmentError) as exc_info:
        start_ipc()

    assert str(exc_info.value) == "AIKIDO_SECRET_KEY is not set."


def test_start_ipc(mocker):
    assert get_ipc() == None
    mocker.patch("os.environ", {"AIKIDO_SECRET_KEY": "mock_key"})

    start_ipc()

    assert get_ipc() != None
    assert get_ipc().address == IPC_ADDRESS
    assert get_ipc().key == b"mock_key"

    get_ipc().agent_proc.kill()


def test_send_data_exception(monkeypatch, caplog):
    def mock_client(address, authkey):
        raise Exception("Connection Error")

    monkeypatch.setitem(globals(), "Client", mock_client)
    monkeypatch.setitem(globals(), "logger", caplog)

    ipc = IPC(("localhost", 9898), "mock_key")
    ipc.send_data("ACTION", "Test Object")

    assert "Failed to send data to agent" in caplog.text
    # Add assertions for handling exceptions
