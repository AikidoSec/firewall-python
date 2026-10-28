"""Helper function file, see function docstring"""

from aikido_zen.background_process.ipc import IPCClient
from aikido_zen.background_process.commands import read_property
from aikido_zen.helpers.check_env_for_blocking import check_env_for_blocking


def is_blocking_enabled():
    """
    Checks with the background process if blocking is enabled
    """
    ipc = IPCClient.get()
    if ipc:
        should_block_res = ipc.send_message(read_property.generate("block"))
        if should_block_res["success"]:
            return should_block_res["data"]
    return check_env_for_blocking()
