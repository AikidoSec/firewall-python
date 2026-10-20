import os
import threading
import time
from queue import Full, Queue

from aikido_zen.background_process.socket_connection import open_connection
from aikido_zen.helpers.ipc.command_types import Payload
from aikido_zen.helpers.logging import logger

MAX_PENDING_EVENTS = 1000


class IPCClient:
    _instance = None

    # Share one worker so replacing a client does not leave another idle thread behind.
    _pid = os.getpid()
    _start_locks = {_pid: threading.Lock()}
    _queue = Queue(maxsize=MAX_PENDING_EVENTS)
    _thread = None
    _warned_full = False

    def __init__(self, address, key):
        self.address = address
        self.key = key

        IPCClient._instance = self

    @staticmethod
    def get():
        return IPCClient._instance

    @staticmethod
    def reset():
        IPCClient._instance = None

    def send_message_async(self, message: Payload):
        """Return local queue acceptance; delivery and its reply run on the worker."""
        if not self.key:
            return {"success": False, "error": "invalid_key"}
        # pylint: disable=protected-access # The alias accesses our own shared class state.
        shared = IPCClient
        try:
            pid = os.getpid()
            start_lock = shared._start_locks.get(pid)
            if start_lock is None:
                # A fork can copy a lock held by a thread that does not survive in the child.
                start_lock = shared._start_locks.setdefault(pid, threading.Lock())

            with start_lock:
                # Pending events belong to the parent, so a forked child must start empty.
                if shared._pid != pid:
                    shared._queue = Queue(maxsize=MAX_PENDING_EVENTS)
                    shared._thread = None
                    shared._warned_full = False
                    shared._pid = pid
                    shared._start_locks = {pid: start_lock}
                if shared._thread is None:
                    thread = threading.Thread(
                        target=shared._send_events,
                        args=(shared._queue,),
                        name="aikido-event-sender",
                        daemon=True,
                    )
                    thread.start()
                    shared._thread = thread
                pending = shared._queue

            pending.put_nowait((self.send_message, message))
            return {"success": True, "queued": True}
        except Full:
            if not shared._warned_full:
                shared._warned_full = True
                logger.warning("Event delivery queue is full; dropping new events.")
            return {"success": False, "error": "queue_full"}
        except Exception as error:
            logger.debug("Could not enqueue event: %s", error)
            return {"success": False, "error": "unknown"}

    def send_message(self, message: Payload):
        try:
            if not self.key:
                # If no key is set, the background process will not start
                return {"success": False, "error": "invalid_key"}

            if message.timeout_in_sec <= 0:
                return {"success": False, "error": "timeout"}
            deadline = time.monotonic() + message.timeout_in_sec

            with open_connection(self.address, deadline) as conn:
                conn.send((message.identifier, message.request))
                result = conn.recv()
            if time.monotonic() >= deadline:
                return {"success": False, "error": "timeout"}
        except Exception as e:
            logger.debug("Exception occurred in IPC call : %s", e)
            return {"success": False, "error": "timeout"}
        return {"success": True, "data": result}

    @staticmethod
    def _send_events(pending):
        while True:
            item = pending.get()
            try:
                if item is None:
                    return
                item[0](item[1])
            except Exception as error:
                logger.debug("Exception occurred in event delivery: %s", error)
            finally:
                # The idle worker must not retain the last request it sent.
                del item
                pending.task_done()
