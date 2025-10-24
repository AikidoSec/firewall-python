"""Exports the function starts_with_unsafe_path"""

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
]

# List of dangerous path starts, including Windows paths
dangerous_path_starts = linux_root_folders + ["c:/", "c:\\"]


def starts_with_unsafe_path(file_path, user_input):
    """Check if the file path starts with any dangerous paths and the user input."""
    path_parsed = ensure_one_leading_slash(file_path.lower())
    input_parsed = ensure_one_leading_slash(user_input.lower())

    for dangerous_start in dangerous_path_starts:
        if path_parsed.startswith(dangerous_start) and path_parsed.startswith(
            input_parsed
        ):
            return True

    return False


def ensure_one_leading_slash(path: str) -> str:
    if path.startswith("/"):
        return "/" + path.lstrip("/")
    return path
