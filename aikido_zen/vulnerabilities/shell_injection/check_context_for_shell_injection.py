"""
This will check the context of the request for shell injection
"""

from aikido_zen.helpers.extract_strings_from_context import extract_strings_from_context
from .detect_shell_injection import detect_shell_injection


def check_context_for_shell_injection(command, operation, context):
    """
    This will check the context of the request for Shell injections
    """
    if not isinstance(command, str):
        # Command must be string to run algorithm
        return {}
    for user_input, path, source in extract_strings_from_context(context):
        if detect_shell_injection(command, user_input):
            return {
                "operation": operation,
                "kind": "shell_injection",
                "source": source,
                "pathToPayload": path,
                "metadata": {"command": command},
                "payload": user_input,
            }
    return {}
