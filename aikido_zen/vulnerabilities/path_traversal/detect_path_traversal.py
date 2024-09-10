"""
Exports `detect_path_traversal`
"""

from .contains_unsafe_path_parts import contains_unsafe_path_parts
from .parse_as_file_url import parse_as_file_url
from .unsafe_path_start import starts_with_unsafe_path


def detect_path_traversal(file_path, user_input, check_path_start=True, is_url=False):
    """Detect potential path traversal vulnerabilities."""
    if len(user_input) <= 1:
        # We ignore single characters since they don't pose a big threat.
        return False

    # Check for URL path traversal
    # Reason: new URL("file:///../../test.txt") => /test.txt
    # The normal check for relative path traversal will fail in this case, because transformed path does not contain ../.
    # For absolute path traversal, we dont need to check the transformed path, because it will always start with /.
    # Also /./ is checked by normal absolute path traversal check (if #219 is merged)
    if is_url and contains_unsafe_path_parts(user_input):
        file_path_from_url = parse_as_file_url(user_input)
        if file_path_from_url and file_path_from_url in file_path:
            return True

    if len(user_input) > len(file_path):
        # We ignore cases where the user input is longer than the file path.
        # Because the user input can't be part of the file path.
        return False

    if user_input not in file_path:
        # We ignore cases where the user input is not part of the file path.
        return False

    if contains_unsafe_path_parts(file_path) and contains_unsafe_path_parts(user_input):
        return True

    if check_path_start:
        return starts_with_unsafe_path(
            file_path, user_input
        )  #  Check for absolute path traversal

    return False
