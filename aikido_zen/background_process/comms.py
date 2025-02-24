"""
Holds the globally stored comms object
Exports the AikidoIPCCommunications class
"""

import multiprocessing.connection as con
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

    def send_data_to_bg_process(self, action, obj, receive=False):
        """Try-catched send_data_to_bg_process"""
        try:
            return self._send_data_to_bg_process(action, obj, receive)
        except Exception as e:
            logger.debug("Exception happened in send_data_to_bg_process : %s", e)
            return {"success": False, "error": "unknown"}

    def _send_data_to_bg_process(self, action, obj, receive=False):
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
                # Create a connection, this can get stuck :
                conn = con.Client(address, authkey=None)

                # Send/Receive data :
                conn.send(data)
                if receive:
                    result_obj[1] = conn.recv()
                # Close the connection :
                conn.close()
                result_obj[0] = True  #  Connection ended gracefully
            except Exception as e:
                logger.debug("Exception occured in thread : %s", e)

        # Create a shared result object between the thread and this process :
        result_obj = [False, None]  # Needs to be an array so we can make a ref.
        t = Thread(
            target=target,
            args=(self.address, self.key, receive, (action, obj), result_obj),
            daemon=True,  #  This allows us to join and set a timeout after which the thread closes
        )

        # Start and join the thread for 100ms, afterwards the thread is forced to close (daemon=True)
        t.start()
        t.join(timeout=0.1)
        if not result_obj[0]:
            logger.debug(
                " Failure in communication to background process, %s(%s)", action, obj
            )
            return {"success": False, "error": "timeout"}

        if receive:
            return {"success": True, "data": result_obj[1]}
        return {"success": True, "data": None}
