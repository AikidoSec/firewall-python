"""Commands __init__.py file"""

from aikido_firewall.helpers.logging import logger
from .attack import process_attack
from .read_property import process_read_property
from .route import process_route
from .user import process_user
from .wrapped_package import process_wrapped_package
from .should_ratelimit import process_should_ratelimit
from .kill import process_kill
from .hostnames_add import process_hostnames_add
from .should_block_user import process_should_block_user
from .statistics import process_statistics
from .is_ip_allowed import process_is_ip_allowed
from .fetch_initial_metadata import process_fetch_initial_metadata

commands_map = {
    # This maps to a tuple : (function, returns_data?)
    # Commands that don't return data :
    "ATTACK": (process_attack, False),
    "ROUTE": (process_route, False),
    "USER": (process_user, False),
    "KILL": (process_kill, False),
    "STATISTICS": (process_statistics, False),
    "HOSTNAMES_ADD": (process_hostnames_add, False),
    # Commands that return data :
    "READ_PROPERTY": (process_read_property, True),
    "WRAPPED_PACKAGE": (process_wrapped_package, True),
    "SHOULD_RATELIMIT": (process_should_ratelimit, True),
    "SHOULD_BLOCK_USER": (process_should_block_user, True),
    "IS_IP_ALLOWED": (process_is_ip_allowed, True),
    "FETCH_INITIAL_METADATA": (process_fetch_initial_metadata, True),
}


def process_incoming_command(connection_manager, obj, conn, queue):
    """Processes an incoming command"""
    action = obj[0]
    data = obj[1]
    if action in commands_map:
        func, returns_data = commands_map[action]
        if returns_data:
            conn.send(func(connection_manager, data, queue))
        func(connection_manager, data, queue)
    else:
        logger.debug("Command : `%s` not found, aborting", action)
