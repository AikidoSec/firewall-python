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


def ipc_address_with_counter(counter):
    """Generates a random UDS file"""
    temp_dir = get_temp_dir()
    prefix = "aikido_python"
    index = str(counter)
    return f"{temp_dir}/{prefix}_{index}.sock"


def start_background_process():
    """
    Starts a process to handle incoming/outgoing data
    """

    # Generate a secret key :
    secret_key_bytes = str.encode(str(get_token_from_env()))

    # Remove the socket file if it already exists
    i = 1
    ipc_address = ipc_address_with_counter(i)
    while os.path.exists(ipc_address):
        # Removing this UDS File will result in that bg process terminating. See
        # aikido_background_process.py > socket_file_exists_check()
        logger.debug(
            "Unix Domain Socket file %s already exists, deleting.", ipc_address
        )
        os.remove(ipc_address)

        i += 1
        ipc_address = ipc_address_with_counter(i)

    logger.debug("Communication starting on UDS File : %s", ipc_address)
    comms = AikidoIPCCommunications(ipc_address, secret_key_bytes)
    comms.start_aikido_listener()
