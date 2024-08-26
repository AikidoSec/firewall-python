"""Exports `process_wrapped_package`"""

from aikido_firewall.helpers.logging import logger


def process_wrapped_package(reporter, data, queue=None):
    """A package has been wrapped"""
    try:
        pkg_name = data["name"]
        pkg_details = data["details"]
        reporter.packages[pkg_name] = pkg_details
        return True
    except KeyError:
        logger.info("Package info was not formatted correctly : %s", data)
        return False
    except AttributeError:
        return False
