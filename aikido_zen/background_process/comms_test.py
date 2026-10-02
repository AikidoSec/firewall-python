import threading
import time

import pytest
import aikido_zen.background_process.comms as comms_module
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


class CollectingConnection:
    def __init__(self, sent, release=None):
        self.sent = sent
        self.release = release

    def send(self, data):
        if self.release:
            self.release.wait()
        self.sent.append(data)

    def close(self):
        pass


def collecting_comms(monkeypatch, release=None):
    sent = []

    class FakeCon:
        @staticmethod
        def Client(address, authkey=None):
            return CollectingConnection(sent, release)

    monkeypatch.setattr(comms_module, "con", FakeCon)
    return AikidoIPCCommunications("localhost", b"mock_key"), sent


def wait_for(predicate, timeout=2):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    return False


def count_senders():
    return sum(
        1 for t in threading.enumerate() if t.name == comms_module.SENDER_THREAD_NAME
    )


def test_an_event_is_delivered_by_the_sender_thread(monkeypatch):
    comms, sent = collecting_comms(monkeypatch)

    result = comms.send_data_to_bg_process("put_event", {"n": 1})

    assert result == {"success": True, "data": None}
    assert wait_for(lambda: sent == [("put_event", {"n": 1})])


def test_events_keep_their_order(monkeypatch):
    comms, sent = collecting_comms(monkeypatch)

    for n in range(20):
        comms.send_data_to_bg_process("put_event", {"n": n})

    assert wait_for(lambda: len(sent) == 20)
    assert [data["n"] for _, data in sent] == list(range(20))


def test_a_stalled_socket_only_ever_uses_one_sender_thread(monkeypatch):
    release = threading.Event()
    before = count_senders()
    comms, _ = collecting_comms(monkeypatch, release=release)
    try:
        for _ in range(200):
            comms.send_data_to_bg_process("put_event", {"n": 1})

        assert count_senders() == before + 1
    finally:
        release.set()


def test_resetting_the_sender_starts_over_with_an_empty_queue(monkeypatch):
    release = threading.Event()
    comms, _ = collecting_comms(monkeypatch, release=release)
    try:
        for _ in range(10):
            comms.send_data_to_bg_process("put_event", {"n": 1})
        before = count_senders()

        comms.reset_sender()

        assert comms._sender.events.empty()
        assert count_senders() == before + 1
    finally:
        release.set()


def test_a_call_that_wants_a_reply_still_waits_for_it(monkeypatch):
    class ReplyingConnection:
        def send(self, data):
            pass

        def recv(self):
            return "the-reply"

        def close(self):
            pass

    class FakeCon:
        @staticmethod
        def Client(address, authkey=None):
            return ReplyingConnection()

    monkeypatch.setattr(comms_module, "con", FakeCon)
    comms = AikidoIPCCommunications("localhost", b"mock_key")

    result = comms.send_data_to_bg_process("PING", tuple(), receive=True)

    assert result == {"success": True, "data": "the-reply"}


def test_a_forked_process_starts_its_own_sender(monkeypatch):
    comms, sent = collecting_comms(monkeypatch)
    comms.send_data_to_bg_process("put_event", {"n": "parent"})
    assert wait_for(lambda: len(sent) == 1)
    before = count_senders()

    monkeypatch.setattr(comms_module.os, "getpid", lambda: comms._sender.pid + 1)
    comms.send_data_to_bg_process("put_event", {"n": "child"})

    assert count_senders() == before + 1
    assert wait_for(lambda: [d[1]["n"] for d in sent] == ["parent", "child"])


def test_a_call_that_gets_no_reply_in_time_reports_a_timeout(monkeypatch):
    release = threading.Event()

    class SilentConnection:
        def send(self, data):
            pass

        def recv(self):
            release.wait()
            return "too-late"

        def close(self):
            pass

    class FakeCon:
        @staticmethod
        def Client(address, authkey=None):
            return SilentConnection()

    monkeypatch.setattr(comms_module, "con", FakeCon)
    comms = AikidoIPCCommunications("localhost", b"mock_key")
    try:
        result = comms.send_data_to_bg_process(
            "SHOULD_RATELIMIT", {}, receive=True, timeout_in_sec=0.01
        )

        assert result == {"success": False, "error": "timeout"}
    finally:
        release.set()


def test_nothing_is_sent_without_a_key():
    comms = AikidoIPCCommunications("localhost", None)

    assert comms.send_data_to_bg_process("PING", tuple(), receive=True) == {
        "success": False,
        "error": "invalid_key",
    }


def test_threads_sending_their_first_event_together_start_one_sender(monkeypatch):
    for _ in range(5):
        before = count_senders()
        comms, sent = collecting_comms(monkeypatch)
        start = threading.Barrier(32)

        def fire(n):
            start.wait()
            comms.send_data_to_bg_process("put_event", {"n": n})

        threads = [threading.Thread(target=fire, args=(n,)) for n in range(32)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert count_senders() == before + 1
        assert wait_for(lambda: len(sent) == 32)


def test_a_send_that_fails_does_not_hold_up_the_next_event(monkeypatch):
    attempts = []

    class RefusingConnection:
        def __init__(self):
            attempts.append(1)

        def send(self, data):
            raise ConnectionRefusedError("the background process is not there")

        def close(self):
            pass

    class FakeCon:
        @staticmethod
        def Client(address, authkey=None):
            return RefusingConnection()

    monkeypatch.setattr(comms_module, "con", FakeCon)
    comms = AikidoIPCCommunications("localhost", b"mock_key")

    for n in range(10):
        comms.send_data_to_bg_process("put_event", {"n": n})

    assert wait_for(lambda: len(attempts) == 10)
    assert comms._sender.events.empty()
