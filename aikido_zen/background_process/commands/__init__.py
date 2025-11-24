from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.ipc.command_types import CommandContext
from .put_event import PutEventCommand
from .check_firewall_lists import process_check_firewall_lists
from .read_property import process_read_property
from .should_ratelimit import process_should_ratelimit
from .ping import process_ping
from .sync_data import process_sync_data

commands_map = {
    "SYNC_DATA": process_sync_data,
    "READ_PROPERTY": process_read_property,
    "SHOULD_RATELIMIT": process_should_ratelimit,
    "PING": process_ping,
    "CHECK_FIREWALL_LISTS": process_check_firewall_lists,
}

modern_commands = [PutEventCommand]


def process_incoming_command(connection_manager, obj, conn, queue):
    inbound_identifier = obj[0]
    inbound_request = obj[1]
    if inbound_identifier in commands_map:
        func = commands_map[inbound_identifier]
        return conn.send(func(connection_manager, inbound_identifier, queue))

    for cmd in modern_commands:
        if cmd.identifier() == inbound_identifier:
            cmd.run(CommandContext(connection_manager, queue, conn), inbound_request)
            return None

    logger.debug("Command : `%s` not found - did not execute", inbound_identifier)
    return None
