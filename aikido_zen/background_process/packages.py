"""Helper functions for packages"""

import importlib.metadata as metadata
from packaging.version import Version
from aikido_zen.helpers.logging import logger
import aikido_zen.background_process.comms as comms

MAX_REPORT_TRIES = 5

# If any version is supported, this constant can be used
ANY_VERSION = "0.0.0"


def pkg_compat_check(pkg_name, required_version):
    """Reports a newly wrapped package to the bg process"""
    # Fetch package version :
    try:
        pkg_version = metadata.version(pkg_name)
    except metadata.PackageNotFoundError:
        logger.debug(
            "Package `%s` was wrapped but could not find a version, not monkeypatching.",
            pkg_name,
        )
        return False  # We don't support it since we are not sure what it is.

    # Check if the package version is supported :
    version_supported = is_version_supported(pkg_version, required_version)
    if version_supported:
        logger.info("Wrapped pkg `%s` version (%s)", pkg_name, pkg_version)
    else:
        logger.info("pkg `%s` version %s is not supported.", pkg_name, pkg_version)

    # Try reporting the wrapping of the package 5 times :
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
                    "supported": version_supported,
                },
            },
            True,
        )
        if res["success"] and res["data"] is True:
            break
        attempts += 1

    return version_supported


def is_version_supported(pkg_verion, required_version):
    """Checks if the package version is supported"""
    return Version(pkg_verion) >= Version(required_version)
