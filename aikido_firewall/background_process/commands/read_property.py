"""Mainly exports process_read_property"""

from aikido_firewall.helpers.logging import logger


def process_read_property(bg_process, data, conn):
    """
    Takes in one arg : name of property on reporter, tries to read it.
    Meant to get config props
    """
    try:
        conn.send(bg_process.reporter.__dict__[data])
    except KeyError:
        logger.debug(
            "Reporter has no attribute %s, current reporter: %s",
            data,
            bg_process.reporter,
        )
        conn.send(None)
