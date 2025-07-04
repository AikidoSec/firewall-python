"""Helper functions for packages"""

import importlib.metadata as importlib_metadata

from packaging.version import Version

import aikido_zen.helpers.get_current_unixtime_ms as t
from aikido_zen.helpers.logging import logger

# If any version is supported, this constant can be used
ANY_VERSION = "0.0.0"


def is_package_compatible(package=None, required_version=ANY_VERSION, packages=None):
    """Checks for compatibility of one or multiple package names (in the case of psycopg, you need to check multiple names)"""
    # Fetch package version :
    if package is not None:
        packages = [package]
    if packages is None:
        return False  # no package names provided, return false.
    try:
        for package in packages:
            # Checks if we already looked up the package :
            if PackagesStore.get_package(package) is not None:
                package_version = PackagesStore.get_package(package)["version"]
                return is_version_supported(package_version, required_version)

            # Safely get the package version, with an exception for when the package was not found
            try:
                package_version = importlib_metadata.version(package)
            except importlib_metadata.PackageNotFoundError:
                continue

            # Check support and store package for later
            supported = is_version_supported(package_version, required_version)
            PackagesStore.add_package(package, package_version)

            if supported:
                logger.debug(
                    "Instrumentation for %s=%s supported", package, package_version
                )
                return True

        # No match found
        logger.info("Zen does not support current version of %s", "/".join(packages))
        return False
    except Exception as e:
        logger.debug("Exception occurred in is_package_compatible: %s", e)
        return False  # We don't support it, since something unexpected happened in checking compatibility.


def is_version_supported(version, required_version):
    """Checks if the package version is supported"""
    return Version(version) >= Version(required_version)


# packages store, uses python's built in GlobalInterpreterLock (GIL)
packages = dict()


class PackagesStore:
    @staticmethod
    def export():
        global packages
        result = []
        for package in packages.values():
            if package.get("cleared", False):
                continue
            result.append(dict(package))
        return result

    @staticmethod
    def add_package(package, version):
        global packages
        packages[package] = {
            "name": package,
            "version": version,
            "requiredAt": t.get_unixtime_ms(),
            "cleared": False,
        }

    @staticmethod
    def get_package(package_name):
        global packages
        if package_name in packages:
            return packages[package_name]
        return None

    @staticmethod
    def clear():
        # To clear we set the `cleared` attribute to True
        # This is to ensure you can still get the packages
        # But that they will not show up during an export
        global packages
        for package in packages:
            packages[package]["cleared"] = True

    @staticmethod
    def import_list(imported_packages):
        for package in imported_packages:
            if PackagesStore.get_package(package["name"]):
                continue
            global packages
            packages[package["name"]] = package
