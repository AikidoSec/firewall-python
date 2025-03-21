"""Helper functions for packages"""

import importlib.metadata as importilb_metadata
import importlib.util as importlib_util
from packaging.version import Version
from aikido_zen.helpers.logging import logger
import aikido_zen.background_process.comms as comms

MAX_REPORT_TRIES = 5

# If any version is supported, this constant can be used
ANY_VERSION = "0.0.0"


def is_package_compatible(package=None, required_version=ANY_VERSION, packages=None):
    """Reports a newly wrapped package to the bg process"""
    # Fetch package version :
    if package is not None:
        packages = [package]
    if packages is None:
        return False # no package names provided, return false.
    try:
        for package in packages:
            if importlib_util.find_spec(package) is None:
                continue # package name is not installed
            package_version = importilb_metadata.version(package)
            if is_version_supported(package_version, required_version):
                logger.debug("Instrumentation for %s=%s supported", package, package_version)
                return True

        # No match found
        logger.info("Zen does not support %s", packages)
        return False
    except Exception as e:
        logger.debug("Exception occurred in is_package_compatible: %s", e)
        return False  # We don't support it, since something unexpected happened in checking compatibility.

def is_version_supported(version, required_version):
    """Checks if the package version is supported"""
    return Version(version) >= Version(required_version)
