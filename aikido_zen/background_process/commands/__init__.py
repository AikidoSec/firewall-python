"""Commands __init__.py file"""

from aikido_zen.helpers.logging import logger
from .attack import process_attack
from .read_property import process_read_property
from .should_ratelimit import process_should_ratelimit
from .ping import process_ping
from .sync_data import process_sync_data

commands_map = {
    # This maps to a tuple : (function, returns_data?)
    # Commands that don't return data :
    "ATTACK": (process_attack, False),
    # Commands that return data :
    "SYNC_DATA": (process_sync_data, True),
    "READ_PROPERTY": (process_read_property, True),
    "SHOULD_RATELIMIT": (process_should_ratelimit, True),
    "PING": (process_ping, True),
}


def process_incoming_command(connection_manager, obj, conn, queue):
    """Processes an incoming command"""
    action = obj[0]
    data = obj[1]
    if action in commands_map:
        func, returns_data = commands_map[action]
        if returns_data:
            return conn.send(func(connection_manager, data, queue))
        func(connection_manager, data, queue)
    else:
        logger.debug("Command : `%s` not found, aborting", action)
