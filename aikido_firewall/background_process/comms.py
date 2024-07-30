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
        global comms
        comms = self

    def start_aikido_listener(self):
        """This will start the aikido process which listens"""
        pid = os.fork()
        if pid == 0:  # Child process
            AikidoBackgroundProcess(self.address, self.key)
        else:  # Parent process
            logger.debug("Started background process, PID: %d", pid)

    def send_data_to_bg_process(self, action, obj):
        """
        This creates a new client for comms to the background process
        """

        # We want to make sure that sending out this data affects the process as little as possible
        # So we run it inside a seperate thread with a timeout of 3 seconds
        def target(address, key, data_array):
            try:
                conn = con.Client(address, authkey=key)
                logger.debug("Created connection %s", conn)
                for data in data_array:
                    conn.send(data)
                conn.send(("CLOSE", {}))
                conn.close()
                logger.debug("Connection closed")
            except Exception as e:
                logger.info("Failed to send data to bg process : %s", e)

        t = Thread(
            target=target, args=(self.address, self.key, [(action, obj)]), daemon=True
        )
        t.start()
        t.join(timeout=3)
