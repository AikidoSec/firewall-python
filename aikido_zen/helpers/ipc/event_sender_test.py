import gc
import os
import threading
import weakref
from unittest.mock import Mock

import pytest

from aikido_zen.background_process.comms import AikidoIPCCommunications
from aikido_zen.background_process import comms as communications
from aikido_zen.helpers.ipc import event_sender as module


@pytest.fixture
def sender():
    instance = module.EventSender()
    yield instance
    if instance._thread is not None:
        instance._queue.put(None, timeout=5)
        instance._thread.join(5)
        assert not instance._thread.is_alive()


def assert_drained(sender):
    with sender._queue.all_tasks_done:
        assert sender._queue.all_tasks_done.wait_for(
            lambda: sender._queue.unfinished_tasks == 0, timeout=5
        )


def test_events_return_while_delivery_is_stalled_and_use_one_worker(sender):
    entered = threading.Event()
    resume = threading.Event()
    worker_ids = []

    def deliver(*args, **kwargs):
        worker_ids.append(threading.get_ident())
        entered.set()
        assert resume.wait(5)

    comms = Mock()
    comms.send_data_to_bg_process.side_effect = deliver
    try:
        assert sender.enqueue(comms, "put_event", 0) == {
            "success": True,
            "queued": True,
        }
        assert entered.wait(5)
        first_worker = sender._thread
        for index in range(1, 20):
            assert sender.enqueue(comms, "put_event", index)["success"]
        assert comms.send_data_to_bg_process.call_count == 1
        assert sender._thread is first_worker
    finally:
        resume.set()
    assert_drained(sender)
    assert worker_ids == [first_worker.ident] * 20
    assert [
        call.args[1] for call in comms.send_data_to_bg_process.call_args_list
    ] == list(range(20))
    assert all(
        call.kwargs["timeout_in_sec"] == 5
        for call in comms.send_data_to_bg_process.call_args_list
    )


def test_queue_full_drops_new_events_without_waiting(sender, caplog):
    class Payload:
        pass

    entered = threading.Event()
    resume = threading.Event()
    comms = Mock()

    def deliver(*args, **kwargs):
        entered.set()
        assert resume.wait(5)

    comms.send_data_to_bg_process.side_effect = deliver
    try:
        sender.enqueue(comms, "put_event", 0)
        assert entered.wait(5)
        for index in range(module.MAX_PENDING_EVENTS):
            assert sender.enqueue(comms, "put_event", index + 1)["success"]
        for _ in range(3):
            assert sender.enqueue(comms, "put_event", "overflow") == {
                "success": False,
                "error": "queue_full",
            }
        dropped = Payload()
        dropped_reference = weakref.ref(dropped)
        assert not sender.enqueue(comms, "put_event", dropped)["success"]
        del dropped
        gc.collect()
        assert dropped_reference() is None
        assert sender._queue.qsize() == module.MAX_PENDING_EVENTS
        assert caplog.text.count("Event delivery queue is full") == 1
    finally:
        resume.set()
    assert_drained(sender)
    assert comms.send_data_to_bg_process.call_count == module.MAX_PENDING_EVENTS + 1


@pytest.mark.parametrize("fail", [False, True])
def test_idle_worker_releases_payloads_after_delivery_or_failure(sender, fail):
    class Payload:
        pass

    delivered = []

    class Comms:
        def send_data_to_bg_process(self, action, obj, timeout_in_sec):
            delivered.append(weakref.ref(obj))
            if fail:
                raise OSError("closed socket")

    comms = Comms()
    for _ in range(20):
        sender.enqueue(comms, "put_event", Payload())
    assert_drained(sender)
    gc.collect()
    assert len(delivered) == 20
    assert all(reference() is None for reference in delivered)
    assert sender._thread.is_alive()


def test_invalid_key_does_not_start_the_event_sender(monkeypatch):
    enqueue = Mock()
    monkeypatch.setattr(module.event_sender, "enqueue", enqueue)
    comms = AikidoIPCCommunications(("127.0.0.1", 1), None)
    assert comms.enqueue_event("put_event", None) == {
        "success": False,
        "error": "invalid_key",
    }
    enqueue.assert_not_called()


def test_worker_start_failure_does_not_escape_into_the_application(sender, monkeypatch):
    monkeypatch.setattr(communications, "event_sender", sender)
    monkeypatch.setattr(
        module.threading.Thread, "start", Mock(side_effect=RuntimeError("no threads"))
    )
    comms = AikidoIPCCommunications(("127.0.0.1", 1), b"fixture")
    assert comms.enqueue_event("put_event", None) == {
        "success": False,
        "error": "unknown",
    }
    assert sender._thread is None


def test_pid_change_replaces_inherited_locks_and_drops_inherited_events(sender):
    old_queue = sender._queue
    old_queue.put((None, "put_event", "parent event"))
    old_lock = sender._start_locks[os.getpid()]
    old_lock.acquire()
    sender._pid = os.getpid() - 1
    sender._start_locks = {sender._pid: old_lock}
    comms = Mock()
    try:
        assert sender.enqueue(comms, "put_event", "child event")["success"]
    finally:
        old_lock.release()
    assert_drained(sender)
    assert sender._queue is not old_queue
    assert sender._start_locks[os.getpid()] is not old_lock
    comms.send_data_to_bg_process.assert_called_once_with(
        "put_event", "child event", timeout_in_sec=5
    )


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
    comms = Mock()
    results = []

    def enqueue(index):
        barrier.wait(5)
        results.append(sender.enqueue(comms, "put_event", index))

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
    assert comms.send_data_to_bg_process.call_count == 20


def test_concurrent_producers_start_only_one_worker(sender):
    barrier = threading.Barrier(21)
    workers = set()
    comms = Mock()
    comms.send_data_to_bg_process.side_effect = lambda *args, **kwargs: workers.add(
        threading.get_ident()
    )

    def enqueue():
        barrier.wait(5)
        sender.enqueue(comms, "put_event", None)

    producers = [threading.Thread(target=enqueue) for _ in range(20)]
    for producer in producers:
        producer.start()
    barrier.wait(5)
    for producer in producers:
        producer.join(5)
        assert not producer.is_alive()
    assert_drained(sender)
    assert workers == {sender._thread.ident}
    assert comms.send_data_to_bg_process.call_count == 20
