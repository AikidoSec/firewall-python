from aikido_zen.background_process import AikidoIPCCommunications
from aikido_zen.helpers.ipc.command_types import Payload


def send_payload(
    comms: AikidoIPCCommunications, payload: Payload, timeout_in_sec: float = 0.1
):
    return comms.send_data_to_bg_process(
        payload.identifier,
        payload.request,
        payload.returns_data,
        timeout_in_sec=timeout_in_sec,
    )
