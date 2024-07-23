import pytest
from aikido_firewall.agent import IPC, start_ipc, get_ipc, IPC_ADDRESS


def test_ipc_init():
    address = ("localhost", 9898)
    key = "secret_key"
    ipc = IPC(address, key)

    assert ipc.address == address
    assert ipc.key == b"secret_key"  # Ensure key is encoded as bytes
    assert ipc.agent_proc is None


def test_start_ipc(mocker):
    assert get_ipc() == None
    mocker.patch("os.environ", {"AIKIDO_SECRET_KEY": "mock_key"})

    start_ipc()

    assert get_ipc() != None
    assert get_ipc().address == IPC_ADDRESS
    assert get_ipc().key == b"mock_key"

    get_ipc().agent_proc.kill()
