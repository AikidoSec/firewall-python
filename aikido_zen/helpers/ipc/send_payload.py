from aikido_zen.background_process import AikidoIPCCommunications
from aikido_zen.helpers.ipc.command_types import Payload


def send_payload(comms: AikidoIPCCommunications, payload: Payload):
    return comms.send_data_to_bg_process(
        payload.identifier, payload.request, payload.returns_data
    )
