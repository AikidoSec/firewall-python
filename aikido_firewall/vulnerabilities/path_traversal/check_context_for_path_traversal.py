"""Exports `check_context_for_path_traversal`"""

from aikido_firewall.helpers.extract_strings_from_user_input import (
    extract_strings_from_user_input,
)
from aikido_firewall.helpers.logging import logger
from aikido_firewall.context import UINPUT_SOURCES as SOURCES
from aikido_firewall.helpers.try_parse_url import try_parse_url
from aikido_firewall.helpers.path_to_string import path_to_string
from .detect_path_traversal import detect_path_traversal


def check_context_for_path_traversal(
    filename, operation, context, check_path_start=True
):
    """
    This will check the context for path traversal
    """
    is_url = try_parse_url(filename) is not None
    path_string = path_to_string(filename)
    print(path_string)
    if not path_string:
        return {}

    for source in SOURCES:
        logger.debug("Checking source %s for path traversal", source)
        if hasattr(context, source):
            user_inputs = extract_strings_from_user_input(getattr(context, source))
            for user_input, path in user_inputs.items():
                if detect_path_traversal(
                    path_string, user_input, check_path_start, is_url
                ):
                    return {
                        "operation": operation,
                        "kind": "path_traversal",
                        "source": source,
                        "pathToPayload": path,
                        "metadata": {"filename": path_string},
                        "payload": user_input,
                    }
    return {}