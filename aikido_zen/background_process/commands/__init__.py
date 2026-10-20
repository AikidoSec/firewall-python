from aikido_zen.helpers.logging import logger
from . import (
    check_firewall_lists,
    ping,
    put_event,
    read_property,
    should_ratelimit,
    sync_data,
)

commands_map = {
    check_firewall_lists.IDENTIFIER: check_firewall_lists.process,
    ping.IDENTIFIER: ping.process,
    put_event.IDENTIFIER: put_event.process,
    read_property.IDENTIFIER: read_property.process,
    should_ratelimit.IDENTIFIER: should_ratelimit.process,
    sync_data.IDENTIFIER: sync_data.process,
}


def process_incoming_command(connection_manager, obj, conn, queue):
    inbound_identifier = obj[0]
    inbound_request = obj[1]
    if inbound_identifier in commands_map:
        func = commands_map[inbound_identifier]
        return conn.send(func(connection_manager, inbound_request, queue))

    logger.debug("Command : `%s` not found - did not execute", inbound_identifier)
    return None
