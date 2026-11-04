import io
import multiprocessing.connection as con
import socket
import time
from contextlib import contextmanager


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


@contextmanager
def open_connection(address, deadline):
    with socket.socket(getattr(socket, con.address_type(address))) as sock:
        connect_with_deadline(sock, address, deadline)
        with SocketConnection(sock, deadline) as connection:
            yield connection
