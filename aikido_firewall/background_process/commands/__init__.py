"""Commands __init__.py file"""

from aikido_firewall.helpers.logging import logger
from .attack import process_attack
from .read_property import process_read_property
from .route import process_route
from .user import process_user
from .wrapped_package import process_wrapped_package
from .should_ratelimit import process_should_ratelimit
from .kill import process_kill
from .force_protection_off import process_force_protection_off
from .hostnames_add import process_hostnames_add
from .should_block_user import process_should_block_user
from .statistics import process_statistics
from .is_bypassed_ip import process_is_bypassed_ip

commands_map = {
    "ATTACK": process_attack,
    "READ_PROPERTY": process_read_property,
    "ROUTE": process_route,
    "USER": process_user,
    "WRAPPED_PACKAGE": process_wrapped_package,
    "SHOULD_RATELIMIT": process_should_ratelimit,
    "KILL": process_kill,
    "FORCE_PROTECTION_OFF?": process_force_protection_off,
    "HOSTNAMES_ADD": process_hostnames_add,
    "SHOULD_BLOCK_USER": process_should_block_user,
    "STATISTICS": process_statistics,
    "IS_BYPASSED_IP": process_is_bypassed_ip,
}


def process_incoming_command(bg_process, obj, conn):
    """Processes an incoming command"""
    action = obj[0]
    data = obj[1]
    if action in commands_map:
        commands_map[action](bg_process, data, conn)
    else:
        logger.info("Command : `%s` not found, aborting", action)
