"""
Holds the globally stored comms object
Exports the AikidoIPCCommunications class
"""

import multiprocessing.connection as con
import socket
import struct
from threading import Thread
from aikido_zen.helpers.logging import logger

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


def connect(address, timeout_in_sec):
    """con.Client() with a timeout: con.Client() can block forever on connect."""
    family = con.address_type(address)
    with socket.socket(getattr(socket, family)) as s:
        if family == "AF_UNIX":
            # settimeout() would make a connect to a full queue fail at once on
            # Linux. SO_SNDTIMEO waits for room, up to the timeout.
            sec = int(timeout_in_sec)
            usec = int((timeout_in_sec - sec) * 1_000_000)
            timeval = struct.pack("ll", sec, usec)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDTIMEO, timeval)
            s.connect(address)
            # Left on, the limit would cut off a large send to a busy process.
            s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDTIMEO, struct.pack("ll", 0, 0))
        else:
            s.settimeout(timeout_in_sec)
            s.connect(address)
            s.setblocking(True)
        return con.Connection(s.detach())


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

    def send_data_to_bg_process(self, action, obj, receive=False, timeout_in_sec=0.1):
        """Try-catched send_data_to_bg_process"""
        try:
            return self._send_data_to_bg_process(action, obj, receive, timeout_in_sec)
        except Exception as e:
            logger.debug("Exception happened in send_data_to_bg_process : %s", e)
            return {"success": False, "error": "unknown"}

    def _send_data_to_bg_process(self, action, obj, receive=False, timeout_in_sec=0.1):
        """
        This creates a new client for comms to the background process
        """
        if not self.key:
            # If no key is set, the background process will not start
            return {"success": False, "error": "invalid_key"}

        # We want to make sure that sending out this data affects the process as little as possible
        # So we run it inside a separate thread with a timeout of 100ms
        # If something goes wrong, it will also be encapsulated in the thread i.e. no crashes
        def target(address, key, receive, data, result_obj):
            try:
                # An event keeps waiting to connect, so it still arrives after a freeze.
                if receive:
                    conn = connect(address, timeout_in_sec)
                else:
                    conn = con.Client(address, authkey=None)
                with conn:
                    # Send/Receive data :
                    conn.send(data)
                    if receive:
                        # Without this the thread is stranded when no answer comes.
                        if not conn.poll(timeout_in_sec):
                            return
                        result_obj[1] = conn.recv()
                    result_obj[0] = True  #  Connection ended gracefully
            except Exception as e:
                logger.debug("Exception occurred in thread : %s", e)

        # Create a shared result object between the thread and this process :
        result_obj = [False, None]  # Needs to be an array so we can make a ref.
        t = Thread(
            target=target,
            args=(self.address, self.key, receive, (action, obj), result_obj),
            daemon=True,  #  So an unfinished call never holds up interpreter exit
        )

        # Joining with a timeout only stops us waiting, it does not end the thread.
        t.start()
        t.join(timeout=timeout_in_sec)
        if not result_obj[0]:
            logger.debug(
                " Failure in communication to background process, %s(%s)", action, obj
            )
            return {"success": False, "error": "timeout"}

        if receive:
            return {"success": True, "data": result_obj[1]}
        return {"success": True, "data": None}
