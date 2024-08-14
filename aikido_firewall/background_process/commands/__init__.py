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
from .get_bypassed_ips import process_get_bypassed_ips
from .statistics import process_statistics
from .is_ip_allowed import process_is_ip_allowed
from .match_endpoints import process_match_endpoints

commands_map = {
    "ATTACK": process_attack,
    "READ_PROPERTY": process_read_property,
    "ROUTE": process_route,
    "USER": process_user,
    "WRAPPED_PACKAGE": process_wrapped_package,
    "SHOULD_RATELIMIT": process_should_ratelimit,
    "KILL": process_kill,
    "HOSTNAMES_ADD": process_hostnames_add,
    "SHOULD_BLOCK_USER": process_should_block_user,
    "GET_BYPASSED_IPS": process_get_bypassed_ips,
    "STATISTICS": process_statistics,
    "IS_IP_ALLOWED": process_is_ip_allowed,
    "MATCH_ENDPOINTS": process_match_endpoints,
}


def process_incoming_command(bg_process, obj, conn):
    """Processes an incoming command"""
    action = obj[0]
    data = obj[1]
    if action in commands_map:
        commands_map[action](bg_process, data, conn)
    else:
        logger.info("Command : `%s` not found, aborting", action)
