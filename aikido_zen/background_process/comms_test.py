import threading
import time

import pytest
from aikido_zen.background_process.comms import (
    AikidoIPCCommunications,
    reset_comms,
)


@pytest.fixture(autouse=True)
def reset_comms_after_test():
    yield
    reset_comms()


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


def test_send_data_to_bg_process_does_not_strand_the_thread(mocker):
    release = threading.Event()

    class StalledConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, exc_tb):
            self.close()

        def send(self, data):
            pass

        def poll(self, timeout):
            return False

        def recv(self):
            release.wait()
            return None

        def close(self):
            pass

    mocker.patch("multiprocessing.connection.Client", return_value=StalledConnection())
    comms = AikidoIPCCommunications("localhost", b"mock_key")
    before = threading.active_count()

    try:
        for _ in range(20):
            result = comms.send_data_to_bg_process(
                "CHECK_FIREWALL_LISTS",
                {"ip": "1.2.3.4"},
                receive=True,
                timeout_in_sec=0.01,
            )

        assert result == {"success": False, "error": "timeout"}

        deadline = time.monotonic() + 2
        while threading.active_count() > before and time.monotonic() < deadline:
            time.sleep(0.01)
        assert threading.active_count() == before
    finally:
        release.set()
