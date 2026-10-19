import gc
import socket
import struct
import threading
import time
import weakref
from contextlib import ExitStack, contextmanager
from multiprocessing import connection
from multiprocessing.connection import Listener
from queue import Queue
from types import SimpleNamespace

import pytest

from aikido_zen.background_process import comms as module
from aikido_zen.background_process.commands import process_incoming_command
from aikido_zen.background_process.commands.put_event import PutEventReq


@pytest.fixture(autouse=True)
def reset_comms_after_test():
    yield
    module.reset_comms()


class Payload:
    def __init__(self, size=256 * 1024):
        self.body = bytearray(size)


@pytest.fixture
def resources(monkeypatch):
    sockets = []
    connections = []
    interrupted_sends = []

    class TrackedSocket(socket.socket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            sockets.append(self)

        def sendall(self, *args, **kwargs):
            try:
                return super().sendall(*args, **kwargs)
            except OSError:
                interrupted_sends.append(True)
                raise

    monkeypatch.setattr(
        module,
        "socket",
        SimpleNamespace(**{**vars(socket), "socket": TrackedSocket}),
        raising=False,
    )

    class TrackedConnection(module.SocketConnection):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            connections.append(self)

    monkeypatch.setattr(module, "SocketConnection", TrackedConnection)
    return SimpleNamespace(
        sockets=sockets,
        connections=connections,
        interrupted_sends=interrupted_sends,
    )


def assert_released(resources, payloads):
    gc.collect()
    assert all(sock.fileno() == -1 for sock in resources.sockets)
    assert all(conn.closed for conn in resources.connections)
    assert all(reference() is None for reference in payloads)


class PeerServer:
    def __init__(self, count, reply=b"", read_request=True):
        self.peers = []
        self.count = count
        self.reply = reply
        self.read_request = read_request
        self.finished = threading.Event()
        self.stopped = threading.Event()
        self.listener = socket.socket()
        if not read_request:
            self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(count)
        self.listener.settimeout(0.1)
        self.address = self.listener.getsockname()
        self.thread = threading.Thread(target=self.serve, daemon=True)
        self.thread.start()

    def serve(self):
        try:
            while len(self.peers) < self.count and not self.stopped.is_set():
                try:
                    peer, _ = self.listener.accept()
                except socket.timeout:
                    continue
                self.peers.append(peer)
                request = None
                if self.read_request:
                    with connection.Connection(peer.dup().detach()) as conn:
                        request = conn.recv()
                if callable(self.reply):
                    self.reply(peer, request)
                elif self.reply:
                    peer.sendall(self.reply)
        except (EOFError, OSError):
            pass
        finally:
            self.finished.set()

    def close(self):
        self.stopped.set()
        self.listener.close()
        for peer in self.peers:
            peer.close()
        self.thread.join(1)


@pytest.fixture
def servers():
    instances = []

    def create(*args, **kwargs):
        server = PeerServer(*args, **kwargs)
        instances.append(server)
        return server

    yield create
    for server in instances:
        server.close()


@contextmanager
def full_accept_queue(listener):
    queued = []
    with ExitStack() as stack:
        for _ in range(100):
            peer = stack.enter_context(socket.socket(listener.family))
            peer.settimeout(0.02)
            try:
                peer.connect(listener.getsockname())
            except (BlockingIOError, socket.timeout):
                break
            queued.append(peer)
        else:
            pytest.skip("Could not fill the local accept queue")
        yield queued


def test_comms_init():
    address = ("localhost", 9898)
    key = "secret_key"
    comms = module.AikidoIPCCommunications(address, key)

    assert comms.address == address
    assert comms.key == key


@pytest.mark.parametrize(
    "action,payload,expected",
    [
        ("PING", (), "Received"),
        ("READ_PROPERTY", "block", True),
        ("put_event", PutEventReq({"name": "login.failed"}), None),
    ],
)
def test_commands_return_results_or_acknowledgments(
    resources, servers, monkeypatch, action, payload, expected
):
    events = Queue()

    def respond(peer, request):
        with connection.Connection(peer.dup().detach()) as conn:
            process_incoming_command(SimpleNamespace(block=True), request, conn, events)

    server = servers(1, reply=respond)

    def fail_start(self):
        raise AssertionError("IPC call must not start a thread")

    monkeypatch.setattr(threading.Thread, "start", fail_start)
    communications = module.AikidoIPCCommunications(server.address, b"fixture")
    assert communications.send_data_to_bg_process(
        action, payload, timeout_in_sec=1
    ) == {"success": True, "data": expected}
    if action == "put_event":
        assert events.get_nowait() == {"name": "login.failed"}
    assert_released(resources, [])


@pytest.mark.parametrize(
    "reply",
    [b"", b"\x00", struct.pack("!i", 1000) + b"\x80"],
    ids=["no_reply", "partial_header", "partial_body"],
)
def test_timeout_releases_sockets_and_payloads(resources, servers, reply):
    server = servers(5, reply=reply)
    communications = module.AikidoIPCCommunications(server.address, b"fixture")
    payloads = []
    for _ in range(5):
        payload = Payload()
        payloads.append(weakref.ref(payload))
        assert communications.send_data_to_bg_process(
            "put_event", payload, timeout_in_sec=0.05
        ) == {"success": False, "error": "timeout"}
        del payload

    assert server.finished.wait(1)
    assert len(server.peers) == 5
    assert_released(resources, payloads)
    for peer in server.peers:
        peer.settimeout(1)
        try:
            assert peer.recv(1) == b""
        except ConnectionResetError:
            pass


@pytest.mark.parametrize(
    "reply",
    [b"", b"\x00", struct.pack("!i", 100) + b"\x80"],
    ids=["before_header", "during_header", "during_body"],
)
def test_peer_disconnect_releases_sockets_and_payloads(resources, servers, reply):
    def disconnect(peer, _request):
        if reply:
            peer.sendall(reply)
        peer.shutdown(socket.SHUT_RDWR)
        peer.close()

    server = servers(1, reply=disconnect)
    communications = module.AikidoIPCCommunications(server.address, b"fixture")
    payload = Payload()
    reference = weakref.ref(payload)

    result = communications.send_data_to_bg_process(
        "put_event", payload, timeout_in_sec=1
    )
    assert not result["success"]
    del payload
    assert server.finished.wait(1)
    assert_released(resources, [reference])


def test_send_failure_releases_sockets_and_payloads(resources, servers, monkeypatch):
    def fail_send(self, data):
        raise BrokenPipeError("Peer closed during send")

    monkeypatch.setattr(module.SocketConnection, "_send", fail_send)
    server = servers(1)
    communications = module.AikidoIPCCommunications(server.address, b"fixture")
    payload = Payload()
    reference = weakref.ref(payload)

    result = communications.send_data_to_bg_process(
        "put_event", payload, timeout_in_sec=1
    )
    assert not result["success"]
    del payload
    assert_released(resources, [reference])


def test_connect_failure_closes_socket(resources):
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        communications = module.AikidoIPCCommunications(
            reserved.getsockname(), b"fixture"
        )
        result = communications.send_data_to_bg_process("PING", (), timeout_in_sec=0.1)
        assert not result["success"]
    assert_released(resources, [])


def test_pickle_failure_releases_connection(resources, servers):
    class Unpicklable:
        def __reduce__(self):
            raise ValueError("Cannot serialize payload")

    server = servers(1)
    communications = module.AikidoIPCCommunications(server.address, b"fixture")
    payload = Unpicklable()
    reference = weakref.ref(payload)

    result = communications.send_data_to_bg_process(
        "put_event", payload, timeout_in_sec=1
    )
    assert not result["success"]
    del payload
    assert_released(resources, [reference])


def test_invalid_reply_releases_connection(resources, servers):
    server = servers(1, reply=struct.pack("!i", 4) + b"oops")
    communications = module.AikidoIPCCommunications(server.address, b"fixture")

    result = communications.send_data_to_bg_process("PING", (), timeout_in_sec=1)
    assert not result["success"]
    assert_released(resources, [])


def test_timeout_interrupts_a_blocked_send(resources, servers, monkeypatch):
    create_socket = module.socket.socket

    def small_send_buffer(*args, **kwargs):
        sock = create_socket(*args, **kwargs)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
        return sock

    monkeypatch.setattr(module.socket, "socket", small_send_buffer)
    server = servers(1, read_request=False)
    communications = module.AikidoIPCCommunications(server.address, b"fixture")
    payload = Payload(8 * 1024 * 1024)
    reference = weakref.ref(payload)
    assert communications.send_data_to_bg_process(
        "put_event", payload, timeout_in_sec=0.2
    ) == {"success": False, "error": "timeout"}
    del payload

    assert server.finished.wait(1)
    assert_released(resources, [reference])
    if not resources.interrupted_sends:
        pytest.skip("Local TCP stack buffered the request without blocking send")
    for peer in server.peers:
        peer.settimeout(1)
        assert peer.recv(1)


def test_trickled_reply_does_not_restart_the_timeout(resources, servers):
    def reply(peer, _request):
        peer.sendall(struct.pack("!i", 100))
        for _ in range(100):
            peer.sendall(b"x")
            time.sleep(0.01)

    server = servers(1, reply=reply)
    communications = module.AikidoIPCCommunications(server.address, b"fixture")
    started = time.monotonic()
    assert communications.send_data_to_bg_process("PING", (), timeout_in_sec=0.05) == {
        "success": False,
        "error": "timeout",
    }
    assert_released(resources, [])
    assert time.monotonic() - started < 0.5


@pytest.mark.parametrize("timeout", [0, -1])
def test_expired_call_does_not_open_a_socket(resources, timeout):
    communications = module.AikidoIPCCommunications(("127.0.0.1", 1), b"fixture")

    assert communications.send_data_to_bg_process(
        "PING", (), timeout_in_sec=timeout
    ) == {"success": False, "error": "timeout"}
    assert not resources.sockets


def test_reads_large_reply(resources, servers):
    response = "x" * 1024 * 1024

    def reply(peer, _request):
        with connection.Connection(peer.dup().detach()) as conn:
            conn.send(response)

    server = servers(1, reply=reply)
    communications = module.AikidoIPCCommunications(server.address, b"fixture")
    assert communications.send_data_to_bg_process(
        "READ_PROPERTY", "block", timeout_in_sec=2
    ) == {"success": True, "data": response}
    assert_released(resources, [])


@pytest.mark.parametrize("family", ["AF_INET", "AF_UNIX"])
def test_timeout_releases_payloads_when_accept_queue_is_full(
    resources, tmp_path, family
):
    if family == "AF_UNIX" and not hasattr(socket, "AF_UNIX"):
        pytest.skip("Unix sockets are unavailable")
    with socket.socket(getattr(socket, family)) as listener:
        address = (
            ("127.0.0.1", 0) if family == "AF_INET" else str(tmp_path / "ipc.sock")
        )
        listener.bind(address)
        listener.listen(1)
        with full_accept_queue(listener):
            communications = module.AikidoIPCCommunications(
                listener.getsockname(), b"fixture"
            )
            payloads = []
            for _ in range(3):
                payload = Payload()
                payloads.append(weakref.ref(payload))
                assert communications.send_data_to_bg_process(
                    "put_event", payload, timeout_in_sec=0.05
                ) == {"success": False, "error": "timeout"}
                del payload
            assert_released(resources, payloads)


@pytest.mark.skipif(not hasattr(socket, "AF_UNIX"), reason="Unix sockets unavailable")
def test_queued_connection_succeeds_if_backend_recovers_before_timeout(
    resources, monkeypatch, tmp_path
):
    with socket.socket(socket.AF_UNIX) as listener:
        address = str(tmp_path / "ipc.sock")
        listener.bind(address)
        listener.listen(1)
        listener.settimeout(2)
        accept_calls = threading.Event()
        server_errors = []

        def retry_sleep(duration):
            accept_calls.set()
            time.sleep(duration)

        monkeypatch.setattr(
            module, "time", SimpleNamespace(**{**vars(time), "sleep": retry_sleep})
        )

        def respond():
            try:
                if not accept_calls.wait(2):
                    return
                for _ in queued:
                    peer, _ = listener.accept()
                    peer.close()
                peer, _ = listener.accept()
                with peer, connection.Connection(peer.dup().detach()) as conn:
                    assert conn.recv() == ("PING", ())
                    conn.send("Received")
            except (OSError, AssertionError) as error:
                server_errors.append(repr(error))

        with full_accept_queue(listener) as queued:
            server = threading.Thread(target=respond, daemon=True)
            server.start()
            try:
                communications = module.AikidoIPCCommunications(address, b"fixture")
                assert communications.send_data_to_bg_process(
                    "PING", (), timeout_in_sec=1
                ) == {"success": True, "data": "Received"}
                assert not server_errors
                assert_released(resources, [])
            finally:
                accept_calls.set()
                server.join(3)


def test_concurrent_calls_match_out_of_order_responses():
    listener = Listener(("127.0.0.1", 0), family="AF_INET", backlog=2, authkey=None)
    first_received = threading.Event()
    second_finished = threading.Event()
    allow_first_reply = threading.Event()
    outcomes = {}
    completion_order = []
    properties = SimpleNamespace(first="first response", second="second response")

    def respond():
        with listener.accept() as first_connection:
            first_request = first_connection.recv()
            first_received.set()
            with listener.accept() as second_connection:
                second_request = second_connection.recv()
                second_connection.send(getattr(properties, second_request[1]))
            if allow_first_reply.wait(3):
                first_connection.send(getattr(properties, first_request[1]))

    communications = module.AikidoIPCCommunications(listener.address, b"fixture")

    def request(name):
        outcomes[name] = communications.send_data_to_bg_process(
            "READ_PROPERTY", name, timeout_in_sec=3
        )
        completion_order.append(name)
        if name == "second":
            second_finished.set()

    server = threading.Thread(target=respond, daemon=True)
    first_caller = threading.Thread(target=request, args=("first",), daemon=True)
    second_caller = threading.Thread(target=request, args=("second",), daemon=True)
    server.start()
    first_caller.start()
    try:
        assert first_received.wait(1)
        second_caller.start()
        assert second_finished.wait(1)
        assert "first" not in outcomes
        allow_first_reply.set()
        first_caller.join(2)
        second_caller.join(2)
        assert completion_order == ["second", "first"]
        assert outcomes == {
            "first": {"success": True, "data": "first response"},
            "second": {"success": True, "data": "second response"},
        }
    finally:
        allow_first_reply.set()
        first_caller.join(3)
        if second_caller.ident is not None:
            second_caller.join(3)
        server.join(3)
        listener.close()
