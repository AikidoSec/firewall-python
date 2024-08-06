"""Helper function file, see function docstring"""

from aikido_firewall.background_process import get_comms


def is_blocking_enabled():
    """
    Checks with the background process if blocking is enabled
    """
    should_block_res = get_comms().send_data_to_bg_process(
        action="READ_PROPERTY", obj="block", receive=True
    )
    return should_block_res["success"] and should_block_res["data"]
