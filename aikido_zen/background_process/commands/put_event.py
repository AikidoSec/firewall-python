from aikido_zen.helpers.ipc.command_types import Payload

IDENTIFIER = "put_event"


def generate(event, timeout_in_sec=5) -> Payload:
    return Payload(IDENTIFIER, PutEventReq(event), timeout_in_sec)


def process(connection_manager, request, queue):
    queue.put(request.event)


# IPC uses pickle, so this request class must keep its import path.
class PutEventReq:
    def __init__(self, event):
        # The CloudConnectionManager adds the "agent" field.
        self.event = event
