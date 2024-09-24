"""Exports `check_context_for_path_traversal`"""

from aikido_zen.helpers.extract_strings_from_context import extract_strings_from_context
from aikido_zen.helpers.try_parse_url import try_parse_url
from aikido_zen.helpers.path_to_string import path_to_string
from .detect_path_traversal import detect_path_traversal


def check_context_for_path_traversal(
    filename, operation, context, check_path_start=True
):
    """
    This will check the context for path traversal
    """
    is_url = try_parse_url(filename) is not None
    path_string = path_to_string(filename)
    if not path_string:
        return {}

    for user_input, path, source in extract_strings_from_context(context):
        if detect_path_traversal(path_string, user_input, check_path_start, is_url):
            return {
                "operation": operation,
                "kind": "path_traversal",
                "source": source,
                "pathToPayload": path,
                "metadata": {"filename": path_string},
                "payload": user_input,
            }
    return {}
