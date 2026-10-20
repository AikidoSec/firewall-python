import gc
import os
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
from unittest.mock import Mock

import pytest

from aikido_zen.background_process import ipc as module
from aikido_zen.background_process import socket_connection as transport
from aikido_zen.background_process.commands import ping, put_event, read_property
from aikido_zen.background_process.commands import process_incoming_command


@pytest.fixture(autouse=True)
def reset_ipc_after_test():
    yield
    module.IPCClient.reset()


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
        transport,
        "socket",
        SimpleNamespace(**{**vars(socket), "socket": TrackedSocket}),
        raising=False,
    )

    class TrackedConnection(transport.SocketConnection):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            connections.append(self)

    monkeypatch.setattr(transport, "SocketConnection", TrackedConnection)
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


@pytest.fixture
def sender(monkeypatch):
    shared = module.IPCClient
    monkeypatch.setattr(shared, "_pid", os.getpid())
    monkeypatch.setattr(shared, "_start_locks", {os.getpid(): threading.Lock()})
    monkeypatch.setattr(
        shared, "_queue", module.Queue(maxsize=module.MAX_PENDING_EVENTS)
    )
    monkeypatch.setattr(shared, "_thread", None)
    monkeypatch.setattr(shared, "_warned_full", False)
    yield shared
    if shared._thread is not None:
        shared._queue.put(None, timeout=5)
        shared._thread.join(5)
        assert not shared._thread.is_alive()


def assert_drained(sender):
    with sender._queue.all_tasks_done:
        assert sender._queue.all_tasks_done.wait_for(
            lambda: sender._queue.unfinished_tasks == 0, timeout=5
        )


def test_ipc_init():
    address = ("localhost", 9898)
    key = "secret_key"
    ipc = module.IPCClient(address, key)

    assert ipc.address == address
    assert ipc.key == key
    assert module.IPCClient.get() is ipc
    module.IPCClient.reset()
    assert module.IPCClient.get() is None


@pytest.mark.parametrize(
    "message,expected",
    [
        (ping.generate(timeout_in_sec=1), "Received"),
        (read_property.generate("block", timeout_in_sec=1), True),
        (put_event.generate({"name": "login.failed"}, timeout_in_sec=1), None),
    ],
)
def test_commands_return_results_or_acknowledgments(
    resources, servers, monkeypatch, message, expected
):
    events = Queue()

    def respond(peer, request):
        with connection.Connection(peer.dup().detach()) as conn:
            process_incoming_command(SimpleNamespace(block=True), request, conn, events)

    server = servers(1, reply=respond)

    def fail_start(self):
        raise AssertionError("IPC call must not start a thread")

    monkeypatch.setattr(threading.Thread, "start", fail_start)
    communications = module.IPCClient(server.address, b"fixture")
    assert communications.send_message(message) == {
        "success": True,
        "data": expected,
    }
    if message.identifier == "put_event":
        assert events.get_nowait() == {"name": "login.failed"}
    assert_released(resources, [])


@pytest.mark.parametrize(
    "reply",
    [b"", b"\x00", struct.pack("!i", 1000) + b"\x80"],
    ids=["no_reply", "partial_header", "partial_body"],
)
def test_timeout_releases_sockets_and_payloads(resources, servers, reply):
    server = servers(5, reply=reply)
    communications = module.IPCClient(server.address, b"fixture")
    payloads = []
    for _ in range(5):
        payload = Payload()
        payloads.append(weakref.ref(payload))
        assert communications.send_message(
            put_event.generate(payload, timeout_in_sec=0.05)
        ) == {
            "success": False,
            "error": "timeout",
        }
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
    communications = module.IPCClient(server.address, b"fixture")
    payload = Payload()
    reference = weakref.ref(payload)

    result = communications.send_message(put_event.generate(payload, timeout_in_sec=1))
    assert not result["success"]
    del payload
    assert server.finished.wait(1)
    assert_released(resources, [reference])


def test_send_failure_releases_sockets_and_payloads(resources, servers, monkeypatch):
    def fail_send(self, data):
        raise BrokenPipeError("Peer closed during send")

    monkeypatch.setattr(transport.SocketConnection, "_send", fail_send)
    server = servers(1)
    communications = module.IPCClient(server.address, b"fixture")
    payload = Payload()
    reference = weakref.ref(payload)

    result = communications.send_message(put_event.generate(payload, timeout_in_sec=1))
    assert not result["success"]
    del payload
    assert_released(resources, [reference])


def test_connect_failure_closes_socket(resources):
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        communications = module.IPCClient(reserved.getsockname(), b"fixture")
        result = communications.send_message(ping.generate(timeout_in_sec=0.1))
        assert not result["success"]
    assert_released(resources, [])


def test_pickle_failure_releases_connection(resources, servers):
    class Unpicklable:
        def __reduce__(self):
            raise ValueError("Cannot serialize payload")

    server = servers(1)
    communications = module.IPCClient(server.address, b"fixture")
    payload = Unpicklable()
    reference = weakref.ref(payload)

    result = communications.send_message(put_event.generate(payload, timeout_in_sec=1))
    assert not result["success"]
    del payload
    assert_released(resources, [reference])


def test_invalid_reply_releases_connection(resources, servers):
    server = servers(1, reply=struct.pack("!i", 4) + b"oops")
    communications = module.IPCClient(server.address, b"fixture")

    result = communications.send_message(ping.generate(timeout_in_sec=1))
    assert not result["success"]
    assert_released(resources, [])


def test_timeout_interrupts_a_blocked_send(resources, servers, monkeypatch):
    create_socket = transport.socket.socket

    def small_send_buffer(*args, **kwargs):
        sock = create_socket(*args, **kwargs)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
        return sock

    monkeypatch.setattr(transport.socket, "socket", small_send_buffer)
    server = servers(1, read_request=False)
    communications = module.IPCClient(server.address, b"fixture")
    payload = Payload(8 * 1024 * 1024)
    reference = weakref.ref(payload)
    assert communications.send_message(
        put_event.generate(payload, timeout_in_sec=0.2)
    ) == {
        "success": False,
        "error": "timeout",
    }
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
    communications = module.IPCClient(server.address, b"fixture")
    started = time.monotonic()
    assert communications.send_message(ping.generate(timeout_in_sec=0.05)) == {
        "success": False,
        "error": "timeout",
    }
    assert_released(resources, [])
    assert time.monotonic() - started < 0.5


@pytest.mark.parametrize("timeout", [0, -1])
def test_expired_call_does_not_open_a_socket(resources, timeout):
    communications = module.IPCClient(("127.0.0.1", 1), b"fixture")

    assert communications.send_message(ping.generate(timeout_in_sec=timeout)) == {
        "success": False,
        "error": "timeout",
    }
    assert not resources.sockets


def test_reads_large_reply(resources, servers):
    response = "x" * 1024 * 1024

    def reply(peer, _request):
        with connection.Connection(peer.dup().detach()) as conn:
            conn.send(response)

    server = servers(1, reply=reply)
    communications = module.IPCClient(server.address, b"fixture")
    assert communications.send_message(
        read_property.generate("block", timeout_in_sec=2)
    ) == {
        "success": True,
        "data": response,
    }
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
            communications = module.IPCClient(listener.getsockname(), b"fixture")
            payloads = []
            for _ in range(3):
                payload = Payload()
                payloads.append(weakref.ref(payload))
                assert communications.send_message(
                    put_event.generate(payload, timeout_in_sec=0.05)
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
            transport, "time", SimpleNamespace(**{**vars(time), "sleep": retry_sleep})
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
                communications = module.IPCClient(address, b"fixture")
                assert communications.send_message(ping.generate(timeout_in_sec=1)) == {
                    "success": True,
                    "data": "Received",
                }
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

    communications = module.IPCClient(listener.address, b"fixture")

    def request(name):
        outcomes[name] = communications.send_message(
            read_property.generate(name, timeout_in_sec=3)
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


def test_async_calls_return_while_delivery_is_stalled_and_share_one_worker(
    sender, monkeypatch
):
    entered = threading.Event()
    resume = threading.Event()
    worker_ids = []

    def deliver(*args, **kwargs):
        worker_ids.append(threading.get_ident())
        entered.set()
        assert resume.wait(5)

    ipc = module.IPCClient(("127.0.0.1", 1), b"fixture")
    monkeypatch.setattr(ipc, "send_message", Mock(side_effect=deliver))
    try:
        assert ipc.send_message_async(put_event.generate(0)) == {
            "success": True,
            "queued": True,
        }
        assert entered.wait(5)
        first_worker = sender._thread
        other = module.IPCClient(("127.0.0.1", 2), b"other")
        assert module.IPCClient.get() is other
        monkeypatch.setattr(other, "send_message", Mock(side_effect=deliver))
        for index in range(1, 20):
            assert other.send_message_async(put_event.generate(index))["success"]
        assert ipc.send_message.call_count == 1
        other.send_message.assert_not_called()
        assert sender._thread is first_worker
    finally:
        resume.set()
    assert_drained(sender)
    assert worker_ids == [first_worker.ident] * 20
    calls = ipc.send_message.call_args_list + other.send_message.call_args_list
    assert all(call.args[0].identifier == "put_event" for call in calls)
    assert [call.args[0].request.event for call in calls] == list(range(20))
    assert all(call.args[0].timeout_in_sec == 5 for call in calls)


def test_queue_full_drops_new_events_without_waiting(sender, caplog):
    class Payload:
        pass

    entered = threading.Event()
    resume = threading.Event()
    ipc = module.IPCClient(("127.0.0.1", 1), b"fixture")

    def deliver(*args, **kwargs):
        entered.set()
        assert resume.wait(5)

    ipc.send_message = Mock(side_effect=deliver)
    try:
        ipc.send_message_async(put_event.generate(0))
        assert entered.wait(5)
        for index in range(module.MAX_PENDING_EVENTS):
            assert ipc.send_message_async(put_event.generate(index + 1))["success"]
        for _ in range(3):
            assert ipc.send_message_async(put_event.generate("overflow")) == {
                "success": False,
                "error": "queue_full",
            }
        dropped = Payload()
        dropped_reference = weakref.ref(dropped)
        assert not ipc.send_message_async(put_event.generate(dropped))["success"]
        del dropped
        gc.collect()
        assert dropped_reference() is None
        assert sender._queue.qsize() == module.MAX_PENDING_EVENTS
        assert caplog.text.count("Event delivery queue is full") == 1
    finally:
        resume.set()
    assert_drained(sender)
    assert ipc.send_message.call_count == module.MAX_PENDING_EVENTS + 1


@pytest.mark.parametrize("fail", [False, True])
def test_idle_worker_releases_payloads_after_delivery_or_failure(sender, fail):
    class Payload:
        pass

    delivered = []

    class Comms(module.IPCClient):
        def send_message(self, message):
            delivered.append(
                (
                    weakref.ref(message),
                    weakref.ref(message.request),
                    weakref.ref(message.request.event),
                )
            )
            if fail:
                raise OSError("closed socket")

    ipc = Comms(("127.0.0.1", 1), b"fixture")
    for _ in range(20):
        ipc.send_message_async(put_event.generate(Payload()))
    ipc_reference = weakref.ref(ipc)
    module.IPCClient.reset()
    del ipc
    assert_drained(sender)
    gc.collect()
    assert len(delivered) == 20
    assert all(reference() is None for request in delivered for reference in request)
    assert ipc_reference() is None
    assert sender._thread.is_alive()


def test_invalid_key_does_not_start_the_event_sender(sender, monkeypatch):
    start = Mock()
    monkeypatch.setattr(module.threading.Thread, "start", start)
    ipc = module.IPCClient(("127.0.0.1", 1), None)
    assert ipc.send_message_async(put_event.generate(None)) == {
        "success": False,
        "error": "invalid_key",
    }
    start.assert_not_called()
    assert sender._queue.empty()


def test_worker_start_failure_does_not_escape_into_the_application(sender, monkeypatch):
    monkeypatch.setattr(
        module.threading.Thread, "start", Mock(side_effect=RuntimeError("no threads"))
    )
    ipc = module.IPCClient(("127.0.0.1", 1), b"fixture")
    assert ipc.send_message_async(put_event.generate(None)) == {
        "success": False,
        "error": "unknown",
    }
    assert sender._thread is None


def test_pid_change_replaces_inherited_locks_and_drops_inherited_events(sender):
    old_queue = sender._queue
    old_queue.put((None, put_event.generate("parent event")))
    old_lock = sender._start_locks[os.getpid()]
    old_lock.acquire()
    sender._pid = os.getpid() - 1
    sender._start_locks = {sender._pid: old_lock}
    ipc = module.IPCClient(("127.0.0.1", 1), b"fixture")
    ipc.send_message = Mock()
    message = put_event.generate("child event")
    try:
        assert ipc.send_message_async(message)["success"]
    finally:
        old_lock.release()
    assert_drained(sender)
    assert sender._queue is not old_queue
    assert sender._start_locks[os.getpid()] is not old_lock
    ipc.send_message.assert_called_once_with(message)


def test_concurrent_events_after_a_native_fork_reset_the_sender_only_once(
    sender, monkeypatch
):
    parent_pid = os.getpid() - 1
    sender._pid = parent_pid
    sender._start_locks = {parent_pid: threading.Lock()}
    reset_entered = threading.Event()
    resume_reset = threading.Event()
    queue_factory = module.Queue
    queues = []

    def create_queue(*args, **kwargs):
        queues.append(queue_factory(*args, **kwargs))
        reset_entered.set()
        assert resume_reset.wait(5)
        return queues[-1]

    monkeypatch.setattr(module, "Queue", create_queue)
    barrier = threading.Barrier(21)
    ipc = module.IPCClient(("127.0.0.1", 1), b"fixture")
    ipc.send_message = Mock()
    results = []

    def enqueue(index):
        barrier.wait(5)
        results.append(ipc.send_message_async(put_event.generate(index)))

    producers = [threading.Thread(target=enqueue, args=(index,)) for index in range(20)]
    try:
        for producer in producers:
            producer.start()
        barrier.wait(5)
        assert reset_entered.wait(5)
    finally:
        resume_reset.set()
        for producer in producers:
            producer.join(5)
            assert not producer.is_alive()
    assert_drained(sender)
    assert len(queues) == 1
    assert len(results) == 20
    assert all(result["success"] for result in results)
    assert ipc.send_message.call_count == 20


def test_concurrent_producers_start_only_one_worker(sender):
    barrier = threading.Barrier(21)
    workers = set()
    ipc = module.IPCClient(("127.0.0.1", 1), b"fixture")
    ipc.send_message = Mock(
        side_effect=lambda *args, **kwargs: workers.add(threading.get_ident())
    )

    def enqueue():
        barrier.wait(5)
        ipc.send_message_async(put_event.generate(None))

    producers = [threading.Thread(target=enqueue) for _ in range(20)]
    for producer in producers:
        producer.start()
    barrier.wait(5)
    for producer in producers:
        producer.join(5)
        assert not producer.is_alive()
    assert_drained(sender)
    assert workers == {sender._thread.ident}
    assert ipc.send_message.call_count == 20
