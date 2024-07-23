import pytest
from aikido_firewall.agent import IPC


def test_ipc_init():
    address = ("localhost", 9898)
    key = "secret_key"
    ipc = IPC(address, key)

    assert ipc.address == address
    assert ipc.key == b"secret_key"  # Ensure key is encoded as bytes
    assert ipc.agent_proc is None
