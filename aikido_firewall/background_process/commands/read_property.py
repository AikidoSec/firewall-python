"""Mainly exports process_read_property"""

from aikido_firewall.helpers.logging import logger


def process_read_property(reporter, data, conn):
    """
    Takes in one arg : name of property on reporter, tries to read it.
    Meant to get config props
    """
    try:
        conn.send(reporter.__dict__[data])
    except KeyError:
        logger.debug(
            "Reporter has no attribute %s, current reporter: %s",
            data,
            reporter,
        )
        conn.send(None)
