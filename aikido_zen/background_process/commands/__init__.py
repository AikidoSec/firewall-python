from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.ipc.command_types import CommandContext
from .check_firewall_lists import CheckFirewallListsCommand
from .ping import PingCommand
from .put_event import PutEventCommand
from .read_property import process_read_property
from .should_ratelimit import process_should_ratelimit
from .sync_data import process_sync_data

commands_map = {
    "SYNC_DATA": process_sync_data,
    "READ_PROPERTY": process_read_property,
    "SHOULD_RATELIMIT": process_should_ratelimit,
}

modern_commands = [PutEventCommand, PingCommand, CheckFirewallListsCommand]


def process_incoming_command(connection_manager, obj, conn, queue):
    inbound_identifier = obj[0]
    inbound_request = obj[1]
    if inbound_identifier in commands_map:
        func = commands_map[inbound_identifier]
        return conn.send(func(connection_manager, inbound_request))

    command = None
    for command_option in modern_commands:
        if command_option.identifier() == inbound_identifier:
            command = command_option
    if command is None:
        logger.debug("Command : `%s` not found - did not execute", inbound_identifier)
        return None

    res = command.run(CommandContext(connection_manager, queue, conn), inbound_request)
    if command.returns_data():
        conn.send(res)

    return None
