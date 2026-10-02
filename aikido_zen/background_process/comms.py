"""
Holds the globally stored comms object
Exports the AikidoIPCCommunications class
"""

import multiprocessing.connection as con
import os
from collections import namedtuple
from queue import Queue
from threading import Lock, Thread
from aikido_zen.helpers.logging import logger

# One object, so a reader cannot get the queue of one process and the pid of another.
Sender = namedtuple("Sender", ["pid", "events"])

SENDER_THREAD_NAME = "aikido-ipc-sender"

# pylint: disable=invalid-name # This variable does change
comms = None


def get_comms():
    """
    Returns the globally stored IPC object, which you need
    to communicate to our background process.
    """
    return comms


def reset_comms():
    """This will reset communications"""
    # pylint: disable=global-statement # This needs to be global
    global comms
    if comms:
        logger.debug("Resetting communications. (comms = None)")
        comms = None


class AikidoIPCCommunications:
    """
    Facilitates Inter-Process communication
    """

    def __init__(self, address, key):
        # The key needs to be in byte form
        self.address = address
        self.key = key
        # Set by reset_sender, which the first event triggers.
        self._sender = None
        self._sender_lock = Lock()

        # Set as global ipc object :
        reset_comms()
        # pylint: disable=global-statement # This needs to be global
        global comms
        comms = self

    def send_data_to_bg_process(self, action, obj, receive=False, timeout_in_sec=0.1):
        """Try-catched send_data_to_bg_process"""
        try:
            return self._send_data_to_bg_process(action, obj, receive, timeout_in_sec)
        except Exception as e:
            logger.debug("Exception happened in send_data_to_bg_process : %s", e)
            return {"success": False, "error": "unknown"}

    def reset_sender(self):
        """Starts an empty queue and the thread that sends what goes into it

        Callers hold the sender lock, so a second thread cannot start a second
        sender and leave it waiting on a queue that nothing writes to.
        """
        sender = Sender(os.getpid(), Queue())
        Thread(
            target=self._send_queued_events,
            args=(sender.events,),
            name=SENDER_THREAD_NAME,
            daemon=True,
        ).start()
        self._sender = sender

    def _start_sender(self):
        """Starts this process's sender, unless another thread got there first"""
        with self._sender_lock:
            sender = self._sender
            if sender is None or sender.pid != os.getpid():
                self.reset_sender()
            return self._sender

    def _send_over_socket(self, data, receive=False):
        conn = con.Client(self.address, authkey=None)
        try:
            conn.send(data)
            return conn.recv() if receive else None
        finally:
            # Closed here so a failed send cannot leak the connection.
            conn.close()

    def _send_queued_events(self, events):
        while True:
            # Waits here for the next event, no timeout and no cost while idle.
            data = events.get()
            try:
                self._send_over_socket(data)
            except Exception as e:
                # Caught so the loop carries on with the next event.
                logger.debug("Exception occurred in sender thread : %s", e)

    def _queue_event(self, action, obj):
        """Hands the data to the sender thread without waiting for it to be sent"""
        # A forked worker inherits this object but not the thread draining the queue.
        sender = self._sender
        if sender is None or sender.pid != os.getpid():
            sender = self._start_sender()

        sender.events.put_nowait((action, obj))
        return {"success": True, "data": None}

    def _send_and_wait_for_reply(self, action, obj, timeout_in_sec):
        """Sends the data and waits for the answer, for no longer than the timeout"""
        # We want to make sure that sending out this data affects the process as little as possible
        # So we run it inside a separate thread with a timeout
        # If something goes wrong, it will also be encapsulated in the thread i.e. no crashes
        # Create a shared result object between the thread and this process :
        result_obj = [False, None]  # Needs to be an array so we can make a ref.

        def target():
            try:
                result_obj[1] = self._send_over_socket((action, obj), receive=True)
                result_obj[0] = True  #  Connection ended gracefully
            except Exception as e:
                logger.debug("Exception occurred in thread : %s", e)

        # daemon, so an unfinished call never holds up interpreter exit
        t = Thread(target=target, daemon=True)

        # The thread keeps running after the timeout, we only stop waiting for it.
        t.start()
        t.join(timeout=timeout_in_sec)
        if not result_obj[0]:
            logger.debug(
                " Failure in communication to background process, %s(%s)", action, obj
            )
            return {"success": False, "error": "timeout"}

        return {"success": True, "data": result_obj[1]}

    def _send_data_to_bg_process(self, action, obj, receive=False, timeout_in_sec=0.1):
        """Picks how to reach the background process, based on whether a reply is read"""
        if not self.key:
            # If no key is set, the background process will not start
            return {"success": False, "error": "invalid_key"}

        if not receive:
            # Nothing reads a reply, so the caller does not wait for the socket at all.
            return self._queue_event(action, obj)

        return self._send_and_wait_for_reply(action, obj, timeout_in_sec)
