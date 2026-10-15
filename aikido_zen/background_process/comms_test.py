import multiprocessing.connection as con
import os
import shutil
import socket
import sys
import tempfile
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


class FakeBackgroundProcess:
    def __init__(self, address):
        self.received = []
        self.command_time = 0
        self._stopped = threading.Event()
        self._server = socket.socket(socket.AF_UNIX)
        self._server.bind(address)
        self._server.listen(1)
        self._server.settimeout(0.05)
        self._thread = threading.Thread(target=self._serve, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stopped.set()
        if self._thread.is_alive():
            self._thread.join()
        self._server.close()

    def _serve(self):
        while not self._stopped.is_set():
            try:
                sock, _ = self._server.accept()
            except socket.timeout:
                continue
            with con.Connection(sock.detach()) as conn:
                try:
                    action, data = conn.recv()
                    self.received.append((action, data))
                    time.sleep(0.5 if action == "SLOW" else self.command_time)
                    conn.send("reply")
                except (EOFError, OSError):
                    pass


@pytest.fixture
def background_process():
    # pytest's tmp_path is longer than the socket path limit on macOS.
    tmp_dir = tempfile.mkdtemp(dir="/tmp")
    address = os.path.join(tmp_dir, "aikido.sock")
    # Not started, so it does not accept yet: to callers it looks frozen.
    process = FakeBackgroundProcess(address)
    yield AikidoIPCCommunications(address, b"key"), process
    process.stop()
    shutil.rmtree(tmp_dir)


def check_ip(comms, timeout_in_sec):
    return comms.send_data_to_bg_process(
        "CHECK_FIREWALL_LISTS",
        {"ip": "1.2.3.4"},
        receive=True,
        timeout_in_sec=timeout_in_sec,
    )


def wait_until(condition):
    deadline = time.monotonic() + 2
    while not condition() and time.monotonic() < deadline:
        time.sleep(0.01)
    return condition()


@pytest.mark.skipif(sys.platform != "linux", reason="macOS refuses a full queue")
def test_frozen_background_process_does_not_strand_threads(background_process):
    comms, _ = background_process
    before = threading.active_count()

    results = [check_ip(comms, 0.01) for _ in range(20)]

    assert results == [{"success": False, "error": "timeout"}] * 20
    assert wait_until(lambda: threading.active_count() == before)


@pytest.mark.skipif(sys.platform != "linux", reason="macOS refuses a full queue")
def test_events_sent_while_frozen_arrive_after_resume(background_process):
    comms, process = background_process

    for n in range(20):
        comms.send_data_to_bg_process("put_event", {"n": n}, timeout_in_sec=0.01)
    process.start()

    assert wait_until(lambda: len(process.received) == 20)


@pytest.mark.skipif(sys.platform != "linux", reason="macOS refuses a full queue")
def test_busy_background_process_answers_queued_calls(background_process):
    comms, process = background_process
    process.command_time = 0.005
    process.start()
    results = []

    threads = [
        threading.Thread(target=lambda: results.append(check_ip(comms, 1)))
        for _ in range(20)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results == [{"success": True, "data": "reply"}] * 20


@pytest.mark.skipif(sys.platform == "win32", reason="needs a unix socket")
def test_large_message_to_a_busy_background_process_arrives(background_process):
    comms, process = background_process
    process.start()
    busy = threading.Thread(
        target=comms.send_data_to_bg_process,
        args=("SLOW", {}),
        kwargs={"receive": True, "timeout_in_sec": 1},
    )
    busy.start()
    time.sleep(0.05)
    comms.send_data_to_bg_process(
        "SYNC_DATA", "x" * 1_000_000, receive=True, timeout_in_sec=0.1
    )
    busy.join()

    assert wait_until(lambda: ("SYNC_DATA", "x" * 1_000_000) in process.received)
