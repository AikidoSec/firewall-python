"""Helper functions for packages"""

import importlib.metadata as importlib_metadata
import re

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
        for package_name in packages:
            # Checks if we already looked up the package :
            if PackagesStore.get_package(package_name) is not None:
                package_version = PackagesStore.get_package(package_name)["version"]
                return is_version_supported(package_version, required_version)

            # Safely get the package version, with an exception for when the package was not found
            try:
                package_version = importlib_metadata.version(package_name)
            except importlib_metadata.PackageNotFoundError:
                continue

            # Check support and store package for later
            supported = is_version_supported(package_version, required_version)
            PackagesStore.add_package(package_name, package_version)

            if supported:
                logger.debug(
                    "Instrumentation for %s=%s supported", package_name, package_version
                )
                return True

        # No match found
        logger.info("Zen does not support current version of %s", "/".join(packages))
        return False
    except Exception as e:
        logger.debug("Exception occurred in is_package_compatible: %s", e)
        return False  # We don't support it, since something unexpected happened in checking compatibility.


# PEP 440 version scheme, the same one the packaging library accepts
VERSION_PATTERN = re.compile(
    r"v?(?:([0-9]+)!)?([0-9]+(?:\.[0-9]+)*)"
    r"([-_.]?(?:alpha|a|beta|b|preview|pre|c|rc)[-_.]?[0-9]*)?"
    r"(-[0-9]+|[-_.]?(?:post|rev|r)[-_.]?[0-9]*)?"
    r"([-_.]?dev[-_.]?[0-9]*)?"
    r"(?:\+[a-z0-9]+(?:[-_.][a-z0-9]+)*)?",
    re.IGNORECASE,
)


def is_version_supported(version, required_version):
    """Checks if the package version is supported, required_version is a final release (e.g. 2.8.6)"""
    return parse_version(version) >= parse_version(required_version)


def parse_version(version):
    match = VERSION_PATTERN.fullmatch(version.strip())
    if not match:
        raise ValueError(f"Invalid version: {version}")
    epoch, release, pre, post, dev = match.groups()
    numbers = [int(number) for number in release.split(".")]
    while len(numbers) > 1 and numbers[-1] == 0:
        numbers.pop()
    # Pre-releases (2.8.6rc1) and dev releases (2.8.6.dev0) come before 2.8.6,
    # but a dev release of a post-release (2.8.6.post1.dev0) comes after it.
    is_dev_release = dev is not None and post is None
    is_before_release = pre is not None or is_dev_release
    return int(epoch or 0), numbers, not is_before_release


# packages store, uses python's built in GlobalInterpreterLock (GIL)
packages_store = {}
# version() scans all of sys.path, so names it cannot find (re, json) are looked up once.
names_without_version = set()


class PackagesStore:
    @staticmethod
    def add_installed_package(name):
        if name in names_without_version or name in packages_store:
            return
        version = None
        try:
            version = importlib_metadata.version(name)
        except importlib_metadata.PackageNotFoundError:
            pass
        PackagesStore.add_package(name, version)

    @staticmethod
    def export():
        result = []
        for package in packages_store.values():
            if package.get("cleared", False):
                continue
            result.append(dict(package))
        return result

    @staticmethod
    def add_package(package, version):
        if not version:
            names_without_version.add(package)
            return
        packages_store[package] = {
            "name": package,
            "version": version,
            "requiredAt": t.get_unixtime_ms(),
            "cleared": False,
        }

    @staticmethod
    def get_package(package_name):
        if package_name in packages_store:
            return packages_store[package_name]
        return None

    @staticmethod
    def clear():
        # To clear we set the `cleared` attribute to True
        # This is to ensure you can still get the packages
        # But that they will not show up during an export
        for package in packages_store.values():
            package["cleared"] = True

    @staticmethod
    def clear_names_without_version():
        names_without_version.clear()

    @staticmethod
    def import_list(imported_packages):
        for package in imported_packages:
            if package["name"] in packages_store:
                continue
            packages_store[package["name"]] = package
