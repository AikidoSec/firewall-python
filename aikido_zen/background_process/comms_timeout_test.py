import threading
import weakref
from multiprocessing.connection import Listener

from aikido_zen.background_process import comms as module


class Payload:
    def __init__(self):
        self.body = bytearray(256 * 1024)


def test_stalled_replies_release_threads_connections_and_payloads(
    tmp_path, monkeypatch
):
    count = 20
    listener = Listener(str(tmp_path / "ipc.sock"), family="AF_UNIX", authkey=None)
    accepted = threading.Event()
    connections = []
    threads = []
    references = []
    thread_factory = threading.Thread

    def receive_requests():
        for _ in range(count):
            connection = listener.accept()
            connection.recv()
            connections.append(connection)
        accepted.set()

    def track_thread(*args, **kwargs):
        thread = thread_factory(*args, **kwargs)
        threads.append(thread)
        return thread

    server = thread_factory(target=receive_requests, daemon=True)
    server.start()
    monkeypatch.setattr(module, "Thread", track_thread)
    communications = module.AikidoIPCCommunications(listener.address, b"fixture")
    try:
        for _ in range(count):
            payload = Payload()
            references.append(weakref.ref(payload))
            result = communications.send_data_to_bg_process(
                "SYNC_DATA", payload, receive=True, timeout_in_sec=0.02
            )
            del payload
            assert result == {"success": False, "error": "timeout"}
        assert accepted.wait(2)
        for thread in threads:
            thread.join(0.2)
        assert not any(thread.is_alive() for thread in threads)
        assert all(reference() is None for reference in references)
        assert all(connection.poll(0.2) for connection in connections)
    finally:
        for connection in connections:
            connection.close()
        listener.close()
        server.join(1)
        for thread in threads:
            thread.join(1)
        module.reset_comms()


def test_reply_is_preserved_with_receive_deadline(tmp_path):
    listener = Listener(str(tmp_path / "ipc.sock"), family="AF_UNIX", authkey=None)

    def reply():
        with listener.accept() as connection:
            assert connection.recv() == ("PING", {"value": 1})
            connection.send({"answer": 42})

    server = threading.Thread(target=reply, daemon=True)
    server.start()
    communications = module.AikidoIPCCommunications(listener.address, b"fixture")
    try:
        result = communications.send_data_to_bg_process(
            "PING", {"value": 1}, receive=True, timeout_in_sec=1
        )
        assert result == {"success": True, "data": {"answer": 42}}
    finally:
        server.join(1)
        listener.close()
        module.reset_comms()
