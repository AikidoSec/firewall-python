"""
Holds the globally stored comms object
Exports the AikidoIPCCommunications class
"""

import os
import multiprocessing.connection as con
from threading import Thread
from aikido_firewall.helpers.logging import logger
from aikido_firewall.background_process.aikido_background_process import (
    AikidoBackgroundProcess,
)

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
        comms.send_data_to_bg_process("KILL", {})
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

    def start_aikido_listener(self):
        """This will start the aikido process which listens"""
        pid = os.fork()
        if pid == 0:  # Child process
            AikidoBackgroundProcess(self.address, self.key)
        else:  # Parent process
            logger.debug("Started background process, PID: %d", pid)

    def send_data_to_bg_process(self, action, obj, receive=False):
        """
        This creates a new client for comms to the background process
        """

        # We want to make sure that sending out this data affects the process as little as possible
        # So we run it inside a seperate thread with a timeout of 3 seconds
        # If something goes wrong, it will also be encapsulated in the thread i.e. no crashes
        def target(address, key, receive, data, result_obj):
            # Create a connection, this can get stuck :
            conn = con.Client(address, authkey=key)

            # Send/Receive data :
            conn.send(data)
            if receive:
                result_obj = conn.recv()

            # Close the connection :
            conn.send(("CLOSE", {}))
            conn.close()

        # Create a shared result object between the thread and this process :
        result_obj = None
        t = Thread(
            target=target,
            args=(self.address, self.key, receive, (action, obj), result_obj),
            daemon=True,
        )

        # Start and join the thread for 3 seconds, afterwards the thread is forced to close (daemon=True)
        t.start()
        t.join(timeout=3)
        return result_obj
