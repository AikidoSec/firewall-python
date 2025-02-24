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
        logger.info(
            "Version for %s is undetermined. Zen is unable to protect this module.",
            pkg_name,
        )
        return False  # We don't support it since we are not sure what it is.

    # Check if the package version is supported :
    version_supported = is_version_supported(pkg_version, required_version)
    if version_supported:
        logger.debug("Instrumentation for %s=%s supported", pkg_name, pkg_version)
    else:
        logger.info("Zen does not support %s=%s", pkg_name, pkg_version)
    return version_supported


def is_version_supported(pkg_verion, required_version):
    """Checks if the package version is supported"""
    return Version(pkg_verion) >= Version(required_version)
