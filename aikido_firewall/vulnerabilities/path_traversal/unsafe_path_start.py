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
    lower_case_path = file_path.lower()
    lower_case_user_input = user_input.lower()

    for dangerous_start in dangerous_path_starts:
        if lower_case_path.startswith(dangerous_start) and lower_case_path.startswith(
            lower_case_user_input
        ):
            return True

    return False
