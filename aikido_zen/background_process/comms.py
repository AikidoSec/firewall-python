"""
Holds the globally stored comms object
Exports the AikidoIPCCommunications class
"""

import io
import multiprocessing.connection as con
import socket
import time
from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.ipc.event_sender import event_sender

# pylint: disable=invalid-name # This variable does change
comms = None


class SocketConnection(con.Connection):
    # Keep Connection's framing and pickling while applying deadlines to partial I/O.
    # pylint: disable=arguments-differ
    def __init__(self, sock, deadline):
        self._socket = sock
        self._deadline = deadline
        super().__init__(sock.fileno())

    def _set_timeout(self):
        remaining = self._deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("IPC operation timed out")
        self._socket.settimeout(remaining)

    def _send(self, buf):
        self._set_timeout()
        self._socket.sendall(buf)

    def _recv(self, size):
        buffer = io.BytesIO()
        remaining = size
        while remaining > 0:
            self._set_timeout()
            chunk = self._socket.recv(min(remaining, 65536))
            if not chunk:
                raise EOFError
            buffer.write(chunk)
            remaining -= len(chunk)
        return buffer

    def _close(self):
        self._socket.close()


def connect_with_deadline(sock, address, deadline):
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("IPC connection timed out")
        sock.settimeout(remaining)
        try:
            sock.connect(address)
            sock.setblocking(True)
            return
        except BlockingIOError:
            time.sleep(min(0.001, remaining))


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

        # Set as global ipc object :
        reset_comms()
        # pylint: disable=global-statement # This needs to be global
        global comms
        comms = self

    def enqueue_event(self, action, obj):
        if not self.key:
            return {"success": False, "error": "invalid_key"}
        try:
            return event_sender.enqueue(self, action, obj)
        except Exception as error:
            logger.debug("Could not enqueue event: %s", error)
            return {"success": False, "error": "unknown"}

    def send_data_to_bg_process(self, action, obj, timeout_in_sec=0.1):
        """Try-catched send_data_to_bg_process"""
        try:
            return self._send_data_to_bg_process(action, obj, timeout_in_sec)
        except Exception as e:
            logger.debug("Exception happened in send_data_to_bg_process : %s", e)
            return {"success": False, "error": "unknown"}

    def _send_data_to_bg_process(self, action, obj, timeout_in_sec=0.1):
        """
        This creates a new client for comms to the background process
        """
        if not self.key:
            # If no key is set, the background process will not start
            return {"success": False, "error": "invalid_key"}

        if timeout_in_sec <= 0:
            return {"success": False, "error": "timeout"}
        deadline = time.monotonic() + timeout_in_sec

        with socket.socket(getattr(socket, con.address_type(self.address))) as sock:
            try:
                connect_with_deadline(sock, self.address, deadline)
                with SocketConnection(sock, deadline) as conn:
                    conn.send((action, obj))
                    result = conn.recv()
                if time.monotonic() >= deadline:
                    return {"success": False, "error": "timeout"}
            except Exception as e:
                logger.debug("Exception occurred in IPC call : %s", e)
                return {"success": False, "error": "timeout"}
        return {"success": True, "data": result}
