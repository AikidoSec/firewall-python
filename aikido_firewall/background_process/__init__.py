"""
Aikido background process, this will create a new process
and listen for data sent by our sources and sinks
"""

from aikido_firewall.helpers.token import get_token_from_env
from aikido_firewall.helpers.logging import logger
from aikido_firewall.background_process.comms import (
    AikidoIPCCommunications,
    get_comms,
    reset_comms,
)

IPC_ADDRESS = ("localhost", 9898)  # Specify the IP address and port


def start_background_process():
    """
    Starts a process to handle incoming/outgoing data
    """

    # Generate a secret key :
    secret_key_bytes = str.encode(str(get_token_from_env()))

    comms = AikidoIPCCommunications(IPC_ADDRESS, secret_key_bytes)
    comms.start_aikido_listener()
