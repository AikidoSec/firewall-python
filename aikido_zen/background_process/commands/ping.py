from aikido_zen.helpers.ipc.command_types import Payload

IDENTIFIER = "PING"


def generate(timeout_in_sec=0.1) -> Payload:
    return Payload(IDENTIFIER, (), timeout_in_sec)


def process(connection_manager, request, queue):
    return "Received"
