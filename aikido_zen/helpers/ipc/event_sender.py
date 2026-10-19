import os
import threading
from queue import Full, Queue

from aikido_zen.helpers.logging import logger

MAX_PENDING_EVENTS = 100
EVENT_DELIVERY_TIMEOUT_IN_SEC = 5


class EventSender:
    def __init__(self):
        pid = os.getpid()
        self._start_locks = {pid: threading.Lock()}
        self._reset_queue(pid)

    def _reset_queue(self, pid):
        self._queue = Queue(maxsize=MAX_PENDING_EVENTS)
        self._thread = None
        self._warned_full = False
        self._pid = pid

    def enqueue(self, comms, action, request):
        pid = os.getpid()
        start_lock = self._start_locks.get(pid)
        if start_lock is None:
            # A fork can copy a lock held by a thread that does not survive in the child.
            start_lock = self._start_locks.setdefault(pid, threading.Lock())

        with start_lock:
            # Pending events belong to the parent, so a forked child must start empty.
            if self._pid != pid:
                self._reset_queue(pid)
                self._start_locks = {pid: start_lock}
            if self._thread is None:
                thread = threading.Thread(
                    target=self._send_events,
                    args=(self._queue,),
                    name="aikido-event-sender",
                    daemon=True,
                )
                thread.start()
                self._thread = thread
            pending = self._queue

        try:
            pending.put_nowait((comms, action, request))
            return {"success": True, "queued": True}
        except Full:
            if not self._warned_full:
                self._warned_full = True
                logger.warning("Event delivery queue is full; dropping new events.")
            return {"success": False, "error": "queue_full"}

    @staticmethod
    def _send_events(pending):
        while True:
            item = pending.get()
            try:
                if item is None:
                    return
                item[0].send_data_to_bg_process(
                    item[1], item[2], timeout_in_sec=EVENT_DELIVERY_TIMEOUT_IN_SEC
                )
            except Exception as error:
                logger.debug("Exception occurred in event delivery: %s", error)
            finally:
                # The idle worker must not retain the last request it sent.
                del item
                pending.task_done()


event_sender = EventSender()
