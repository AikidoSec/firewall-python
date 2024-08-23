"""
Aikido background process, this will create a new process
and listen for data sent by our sources and sinks
"""

import os
from aikido_firewall.helpers.token import get_token_from_env
from aikido_firewall.helpers.get_temp_dir import get_temp_dir
from aikido_firewall.helpers.logging import logger
from aikido_firewall.background_process.comms import (
    AikidoIPCCommunications,
    get_comms,
    reset_comms,
)

IPC_ADDRESS = get_temp_dir() + "/aikido_python_socket.sock"


def start_background_process():
    """
    Starts a process to handle incoming/outgoing data
    """

    # Generate a secret key :
    secret_key_bytes = str.encode(str(get_token_from_env()))

    # Remove the socket file if it already exists
    if os.path.exists(IPC_ADDRESS):
        logger.debug("Unix Domain Socket file already exists, deleting.")
        os.remove(IPC_ADDRESS)

    logger.debug("Communication starting on UDS File : %s", IPC_ADDRESS)
    comms = AikidoIPCCommunications(IPC_ADDRESS, secret_key_bytes)
    comms.start_aikido_listener()
