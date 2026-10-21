import aikido_zen.ratelimiting as ratelimiting

from aikido_zen.helpers.ipc.command_types import Payload

IDENTIFIER = "SHOULD_RATELIMIT"


def generate(
    route_metadata, user, group, remote_address, timeout_in_sec=0.01
) -> Payload:
    return Payload(
        IDENTIFIER,
        {
            "route_metadata": route_metadata,
            "user": user,
            "group": group,
            "remote_address": remote_address,
        },
        timeout_in_sec,
    )


def process(connection_manager, request, queue):
    if not connection_manager:
        return False
    return ratelimiting.should_ratelimit_request(
        route_metadata=request["route_metadata"],
        remote_address=request["remote_address"],
        user=request["user"],
        connection_manager=connection_manager,
        group=request["group"],
    )
