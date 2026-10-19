from aikido_zen.background_process import AikidoIPCCommunications
from aikido_zen.helpers.ipc.command_types import Payload


def send_payload(comms: AikidoIPCCommunications, payload: Payload):
    return comms.enqueue_event(
        payload.identifier,
        payload.request,
    )
