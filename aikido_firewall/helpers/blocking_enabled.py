"""Helper function file, see function docstring"""

from aikido_firewall.background_process import get_comms
from aikido_firewall.helpers.check_env_for_blocking import check_env_for_blocking


def is_blocking_enabled():
    """
    Checks with the background process if blocking is enabled
    """
    should_block_res = get_comms().send_data_to_bg_process(
        action="READ_PROPERTY", obj="block", receive=True
    )
    if should_block_res["success"]:
        return should_block_res["data"]
    return check_env_for_blocking()
