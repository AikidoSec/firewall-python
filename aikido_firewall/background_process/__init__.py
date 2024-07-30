"""
Aikido background process, this will create a new process
and listen for data sent by our sources and sinks
"""

import secrets
from aikido_firewall.helpers.logging import logger
from aikido_firewall.background_process.comms import AikidoIPCCommunications

IPC_ADDRESS = ("localhost", 9898)  # Specify the IP address and port


def start_background_process():
    """
    Starts a process to handle incoming/outgoing data
    """

    # Generate a secret key :
    generated_key_bytes = secrets.token_bytes(32)

    comms = AikidoIPCCommunications(IPC_ADDRESS, generated_key_bytes)
    comms.start_aikido_listener()
