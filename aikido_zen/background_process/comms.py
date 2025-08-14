"""
Holds the globally stored comms object
Exports the AikidoIPCCommunications class
"""

import multiprocessing.connection as con
import time
from threading import Thread
from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.run_with_timeout import run_with_timeout

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

    def __init__(self, address):
        # The key needs to be in byte form
        self.address = address
        self.timeout = 100 / 1000  # 100ms

        # Set as global ipc object :
        reset_comms()
        # pylint: disable=global-statement # This needs to be global
        global comms
        comms = self

    def send_data_to_bg_process(self, action, obj, receive=False):
        """
        Try-catched and time-limited send_and_receive_data.

        Args:
            action: The action to perform.
            obj: The object to send.
            receive: Whether to receive data back. (default is False)

        Returns:
            A dictionary indicating success and containing data or error information.
        """
        package = (action, obj)
        args = (self.address, package, receive)

        # Since there is a risk of the connection hanging, we want to send with a timeout
        runner_result = run_with_timeout(
            self.send_and_receive_data, args, timeout=self.timeout
        )
        if runner_result.success():
            return {"success": True, "data": runner_result.result}
        else:
            logger.debug("send_and_receive error: %s", runner_result.error)
            return {"success": False, "error": runner_result.error}

    @staticmethod
    def send_and_receive_data(address, package, should_receive: bool):
        # Establish a connection: possibility that this hangs
        connection = con.Client(address)
        connection.send(package)

        # Optional: receiving data
        result = None
        if should_receive:
            result = connection.recv()

        connection.close()
        return result
