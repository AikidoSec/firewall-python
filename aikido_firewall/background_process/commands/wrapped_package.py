"""Exports `process_wrapped_package`"""

from aikido_firewall.helpers.logging import logger


def process_wrapped_package(connection_manager, data, conn):
    """A package has been wrapped"""
    try:
        pkg_name = data["name"]
        pkg_details = data["details"]
        connection_manager.packages[pkg_name] = pkg_details
        conn.send(True)
    except KeyError:
        logger.info("Package info was not formatted correctly : %s", data)
        conn.send(False)
    except AttributeError:
        conn.send(False)
