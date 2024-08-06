"""Helper functions for packages"""

import importlib.metadata as metadata
from aikido_firewall.helpers.logging import logger
import aikido_firewall.background_process.comms as comms

MAX_REPORT_TRIES = 5


def add_wrapped_package(pkg_name):
    """Reports a newly wrapped package to the bg process"""
    pkg_version = metadata.version(pkg_name)
    logger.info("Successfully wrapped package `%s` version (%s)", pkg_name, pkg_version)
    attempts = 0
    while attempts < MAX_REPORT_TRIES:
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
