"""
Aikido background process, this will create a new process
and listen for data sent by our sources and sinks
"""

import os
from multiprocessing import Process
from aikido_zen.helpers.token import get_token_from_env
from aikido_zen.helpers.get_temp_dir import get_temp_dir
from aikido_zen.helpers.hash_aikido_token import hash_aikido_token
from aikido_zen.helpers.logging import logger

from aikido_zen.background_process.comms import (
    AikidoIPCCommunications,
    get_comms,
    reset_comms,
)
from .aikido_background_process import AikidoBackgroundProcess


def start_background_process():
    """
    Starts a process to handle incoming/outgoing data
    """

    # Generate a secret key :
    secret_key_bytes = str.encode(str(get_token_from_env()))
    if secret_key_bytes == b"None":
        logger.warning(
            "You are running without AIKIDO_TOKEN set, not starting background process.."
        )
        return

    uds_filename = get_uds_filename()
    comms = AikidoIPCCommunications(uds_filename, secret_key_bytes)

    if os.path.exists(uds_filename):
        # Send out a PING to check if the daemon running is still active :
        res = comms.send_data_to_bg_process(action="PING", obj=tuple(), receive=True)
        if res["success"] and res["data"] == "Received":
            # Ping is active, return.
            logger.debug("UDS file exists and is live, returning.")
            return
        # Ping must have failed, remove the existing file to ensure ther eis no corruption.
        os.remove(uds_filename)

    logger.debug("Background process starting on UDS File : %s", uds_filename)
    #  Daemon is set to True so that the process kills itself when the main process dies
    background_process = Process(
        target=AikidoBackgroundProcess, args=(comms.address, comms.key), daemon=True
    )
    background_process.start()


def get_uds_filename():
    """Returns the address for UDS file"""
    temp_dir = get_temp_dir()
    prefix = "aikido_python"
    name = hash_aikido_token()
    return f"{temp_dir}/{prefix}_{name}.sock"
