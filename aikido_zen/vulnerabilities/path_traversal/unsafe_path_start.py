"""Exports the function starts_with_unsafe_path"""

import regex as re

CURRENT_DIR_PATTERN = re.compile(r"/(\./)+")

linux_root_folders = [
    "/bin/",
    "/boot/",
    "/dev/",
    "/etc/",
    "/home/",
    "/init/",
    "/lib/",
    "/media/",
    "/mnt/",
    "/opt/",
    "/proc/",
    "/root/",
    "/run/",
    "/sbin/",
    "/srv/",
    "/sys/",
    "/tmp/",
    "/usr/",
    "/var/",
    # More common in docker apps :
    "/app/",
    "/code/",
]

# List of dangerous path starts, including Windows paths
dangerous_path_starts = linux_root_folders + ["c:/", "c:\\"]


def starts_with_unsafe_path(file_path, user_input):
    """Check if the file path starts with any dangerous paths and the user input."""
    path_parsed = normalize_path(file_path)
    input_parsed = normalize_path(user_input)

    for dangerous_start in dangerous_path_starts:
        if path_parsed.startswith(dangerous_start) and path_parsed.startswith(
            input_parsed
        ):
            return True

    return False


def normalize_path(path: str) -> str:
    """Normalizes a path by lowercasing, removing /./ and removing consecutive slashes"""
    if not path:
        return path

    normalized = path.lower()

    # Matches /./ or /././ or /./././ etc. (one or more ./ sequences after a /)
    normalized = CURRENT_DIR_PATTERN.sub("/", normalized)

    # Merge consecutive slashes since these don't change where you are in the path.
    normalized = re.sub(r"/+", "/", normalized)
    return normalized
