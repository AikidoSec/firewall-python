"""
Aikido background process, this will create a new process
and listen for data sent by our sources and sinks
"""

import hashlib
import multiprocessing
import os
import platform
import sys

from aikido_zen.helpers.token import get_token_from_env
from aikido_zen.helpers.get_temp_dir import get_temp_dir
from aikido_zen.helpers.hash_aikido_token import hash_aikido_token
from aikido_zen.helpers.get_agent_session_id import get_agent_session_id
from aikido_zen.helpers.logging import logger
from aikido_zen.config import PKG_VERSION

from aikido_zen.background_process.ipc import IPCClient
from aikido_zen.background_process.commands import ping
from .aikido_background_process import AikidoBackgroundProcess


def get_process_factory():
    """
    Choose how Zen's background process starts:
    - Use the application's configured method, or Python's default if unset.
    - Use fork instead of forkserver to avoid startup errors caused by
      re-importing the app and calling protect() again.
    - Always use fork under uWSGI; its executable cannot run Python subprocesses.

    The application's own start method is unchanged.
    """
    start_method = multiprocessing.get_start_method(allow_none=True)
    if start_method is None:
        start_method = multiprocessing.get_all_start_methods()[0]
    if start_method == "forkserver" or "uwsgi" in sys.modules:
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

    address = get_socket_path()
    if platform.system() == "Windows":
        # Python does not support Windows UDS just yet, so we have to rely on INET
        address = ("127.0.0.1", 49156)

    ipc = IPCClient(address, secret_key_bytes)

    if isinstance(address, str) and os.path.exists(address):
        if background_process_already_active(ipc):
            return  # Don't start if the background process is already active
        try:
            os.remove(address)
        except FileNotFoundError:
            # Another application worker removed the stale socket first.
            pass

    #  Daemon is set to True so that the process kills itself when the main process dies
    background_process = get_process_factory()(
        target=AikidoBackgroundProcess,
        args=(ipc.address, ipc.key, get_agent_session_id()),
        name="zen-agent-process",
        daemon=True,
    )
    background_process.start()


def get_socket_path():
    temp_dir = get_temp_dir()
    prefix = "aikido_zen"

    # Include the package version to avoid reusing a background process from a previous release.
    identity = f"{hash_aikido_token()}:{PKG_VERSION}"

    name = hashlib.sha256(identity.encode()).hexdigest()
    return f"{temp_dir}/{prefix}_{name}.sock"


def check_socket_access():
    """Returns true if access is possible, false if it's not."""
    filename = get_socket_path()
    directory = "/".join(filename.split("/")[:-1])

    if platform.system() == "Windows":
        # Python does not support Windows UDS just yet, so we have to rely on INET
        return True

    if not os.access(directory, os.R_OK) or not os.access(directory, os.W_OK):
        # We need both read and write permissions in order to start the socket
        logger.critical(
            "Cannot start Zen: no read/write permissions for directory %s. "
            + "You can change the path by setting "
            + "the AIKIDO_TMP_DIR environment variable.",
            directory,
        )
        return False
    return True


def background_process_already_active(ipc):
    res = ipc.send_message(ping.generate())
    if res["success"] and res["data"] == "Received":
        # Ping is active, return.
        logger.debug(
            "A background agent is already running, not starting a new background agent."
        )
        return True
    return False
