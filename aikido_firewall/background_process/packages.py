"""Helper functions for packages"""

import importlib.metadata as metadata
from aikido_firewall.helpers.logging import logger
import aikido_firewall.background_process.comms as comms

MAX_REPORT_TRIES = 5


def add_wrapped_package(pkg_name):
    """Reports a newly wrapped package to the bg process"""
    try:
        pkg_version = metadata.version(pkg_name)
    except metadata.PackageNotFoundError:
        logger.debug(
            "Package `%s` was wrapped but could not find a version, aborting", pkg_name
        )
        return
    logger.info("Successfully wrapped package `%s` version (%s)", pkg_name, pkg_version)
    attempts = 0
    while attempts < MAX_REPORT_TRIES:
        if not comms.get_comms():
            break  # Communications have not been set up.
        res = comms.get_comms().send_data_to_bg_process(
            "WRAPPED_PACKAGE",
            {
                "name": pkg_name,
                "details": {
                    "version": pkg_version,
                    "supported": True,  #  We can change this later if we validate package versions?
                },
            },
            True,
        )
        if res["success"] and res["data"] is True:
            break
        attempts += 1
