from aikido_zen.helpers.ipc.command_types import Payload
from aikido_zen.helpers.logging import logger

IDENTIFIER = "READ_PROPERTY"


def generate(property_name, timeout_in_sec=0.1) -> Payload:
    return Payload(IDENTIFIER, property_name, timeout_in_sec)


def process(connection_manager, request, queue):
    try:
        return connection_manager.__dict__[request]
    except KeyError:
        logger.debug(
            "CloudConnectionManager has no attribute %s, current connection_manager: %s",
            request,
            connection_manager,
        )
        return None
