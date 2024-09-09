import pytest
from aikido_zen.background_process.comms import AikidoIPCCommunications


def test_comms_init():
    address = ("localhost", 9898)
    key = "secret_key"
    comms = AikidoIPCCommunications(address, key)

    assert comms.address == address
    assert comms.key == key


def test_send_data_to_bg_process_exception(monkeypatch, caplog):
    def mock_client(address, authkey):
        raise Exception("Connection Error")

    monkeypatch.setitem(globals(), "Client", mock_client)
    monkeypatch.setitem(globals(), "logger", caplog)

    comms = AikidoIPCCommunications(("localhost", 9898), "mock_key")
    comms.send_data_to_bg_process("ACTION", "Test Object")


def test_send_data_to_bg_process_successful(monkeypatch, caplog, mocker):
    comms = AikidoIPCCommunications(("localhost"), "mock_key")
    mock_client = mocker.MagicMock()
    monkeypatch.setattr("multiprocessing.connection.Client", mock_client)

    # Call the send_data_to_bg_process function
    comms.send_data_to_bg_process("ACTION", {"key": "value"})
