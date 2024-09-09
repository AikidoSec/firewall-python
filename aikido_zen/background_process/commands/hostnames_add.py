"""Exports `process_hostnames_add` function"""

from aikido_zen.helpers.logging import logger


def process_hostnames_add(connection_manager, data, queue=None):
    """Add a hostname to hostnames object in connection_manager"""
    logger.debug("Adding a hostname : %s:%s", data[0], data[1])
    if connection_manager:
        connection_manager.hostnames.add(hostname=data[0], port=data[1])
