from aikido_zen.helpers.ipc.command_types import Payload

IDENTIFIER = "PUT_EVENT"


def generate(event, timeout_in_sec=5) -> Payload:
    return Payload(IDENTIFIER, event, timeout_in_sec)


def process(connection_manager, request, queue):
    queue.put(request)
