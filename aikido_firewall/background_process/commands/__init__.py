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
    "ATTACK": (process_attack, False),
    "READ_PROPERTY": (process_read_property, True),
    "ROUTE": (process_route, False),
    "USER": (process_user, False),
    "WRAPPED_PACKAGE": (process_wrapped_package, True),
    "SHOULD_RATELIMIT": (process_should_ratelimit, True),
    "KILL": (process_kill, False),
    "HOSTNAMES_ADD": (process_hostnames_add, False),
    "SHOULD_BLOCK_USER": (process_should_block_user, True),
    "STATISTICS": (process_statistics, False),
    "IS_IP_ALLOWED": (process_is_ip_allowed, True),
    "FETCH_INITIAL_METADATA": (process_fetch_initial_metadata, True),
}


def process_incoming_command(reporter, obj, conn, queue):
    """Processes an incoming command"""
    action = obj[0]
    data = obj[1]
    if action in commands_map:
        func, returns_data = commands_map[action]
        if returns_data:
            conn.send(func(reporter, data, conn, queue))
        func(reporter, data, conn, queue)
    else:
        logger.debug("Command : `%s` not found, aborting", action)
