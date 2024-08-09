"""Exports `process_hostnames_add` function"""

from aikido_firewall.helpers.logging import logger


def process_hostnames_add(bg_process, data, conn):
    """Add a hostname to hostnames object in reporter"""
    logger.debug("Adding a hostname : %s:%s", data[0], data[1])
    bg_process.reporter.hostnames.add(hostname=data[0], port=data[1])
