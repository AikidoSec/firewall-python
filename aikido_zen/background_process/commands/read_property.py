"""Mainly exports process_read_property"""

from aikido_zen.helpers.logging import logger


def process_read_property(connection_manager, data, queue=None):
    """
    Takes in one arg : name of property on connection_manager, tries to read it.
    Meant to get config props
    """
    try:
        return connection_manager.__dict__[data]
    except KeyError:
        logger.debug(
            "CloudConnectionManager has no attribute %s, current connection_manager: %s",
            data,
            connection_manager,
        )
        return None
