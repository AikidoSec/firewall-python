"""Exports `process_hostnames_add` function"""

from aikido_firewall.helpers.logging import logger


def process_hostnames_add(reporter, data, conn):
    """Add a hostname to hostnames object in reporter"""
    logger.debug("Adding a hostname : %s:%s", data[0], data[1])
    if reporter:
        reporter.hostnames.add(hostname=data[0], port=data[1])
