"""
Aikido background process, this will create a new process
and listen for data sent by our sources and sinks
"""

import multiprocessing
import os
import platform
import sys

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


def get_process_factory():
    """
    Return a process factory that is safe to start while an app is importing.

    Python 3.14 changed the default POSIX start method from fork to forkserver.
    Forkserver re-imports the application's main module, but Zen starts its
    background process while that module is still importing.

    Inspect the configured start method without setting multiprocessing's
    process-wide default. If it is unset, get_all_start_methods() reports the
    platform default as its first entry.
    """
    if sys.version_info >= (3, 14):
        start_method = multiprocessing.get_start_method(allow_none=True)
        if start_method is None:
            start_method = multiprocessing.get_all_start_methods()[0]
        if start_method == "forkserver":
            return multiprocessing.get_context("fork").Process
    return multiprocessing.Process


def start_background_process():
    """
    Starts a process to handle incoming/outgoing data
    """

    # Generate a secret key :
    secret_key_bytes = str.encode(str(get_token_from_env()))
    if secret_key_bytes == b"None":
        logger.warning(
            "You are running without AIKIDO_TOKEN set, not starting background process."
        )
        return

    address = get_uds_filename()
    if platform.system() == "Windows":
        # Python does not support Windows UDS just yet, so we have to rely on INET
        address = ("127.0.0.1", 49156)

    comms = AikidoIPCCommunications(address, secret_key_bytes)

    if isinstance(address, str) and os.path.exists(address):
        if background_process_already_active(comms):
            return  # Don't start if the background process is already active
        try:
            os.remove(address)
        except FileNotFoundError:
            # Another application worker removed the stale socket first.
            pass

    #  Daemon is set to True so that the process kills itself when the main process dies
    background_process = get_process_factory()(
        target=AikidoBackgroundProcess,
        args=(comms.address, comms.key),
        name="zen-agent-process",
        daemon=True,
    )
    background_process.start()


def get_uds_filename():
    """Returns the address for UDS file"""
    temp_dir = get_temp_dir()
    prefix = "aikido_python"
    name = hash_aikido_token()
    return f"{temp_dir}/{prefix}_{name}.sock"


def background_process_already_active(comms):
    res = comms.send_data_to_bg_process(action="PING", obj=tuple(), receive=True)
    if res["success"] and res["data"] == "Received":
        # Ping is active, return.
        logger.debug(
            "A background agent is already running, not starting a new background agent."
        )
        return True
    return False
