"""
Mainly exports `contains_unsafe_path_parts`
"""

dangerous_path_parts = ["../", "..\\"]


def contains_unsafe_path_parts(file_path):
    """Check if the file path contains any dangerous path parts."""
    for dangerous_part in dangerous_path_parts:
        if dangerous_part in file_path:
            return True
    return False
