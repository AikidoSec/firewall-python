"""Helper functions for packages"""

import importlib.metadata as metadata
from packaging.version import Version
from aikido_zen.helpers.logging import logger
import aikido_zen.background_process.comms as comms

MAX_REPORT_TRIES = 5


def add_wrapped_package(pkg_name, required_version="0.0.0"):
    """Reports a newly wrapped package to the bg process"""
    try:
        pkg_version = metadata.version(pkg_name)
    except metadata.PackageNotFoundError:
        logger.debug(
            "Package `%s` was wrapped but could not find a version, not monkeypatching.",
            pkg_name,
        )
        return False  # We don't support it since we are not sure what it is.
    logger.info("Successfully wrapped package `%s` version (%s)", pkg_name, pkg_version)
    attempts = 0
    version_support = is_version_supported(pkg_version, required_version)
    while attempts < MAX_REPORT_TRIES:
        if not comms.get_comms():
            break  # Communications have not been set up.
        res = comms.get_comms().send_data_to_bg_process(
            "WRAPPED_PACKAGE",
            {
                "name": pkg_name,
                "details": {
                    "version": pkg_version,
                    "supported": version_support,
                },
            },
            True,
        )
        if res["success"] and res["data"] is True:
            break
        attempts += 1
    return version_support


def is_version_supported(pkg_verion, required_version):
    """Checks if the package version is supported"""
    return Version(pkg_verion) >= Version(required_version)
