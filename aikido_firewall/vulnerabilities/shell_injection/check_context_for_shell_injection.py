"""
This will check the context of the request for shell injection
"""

from aikido_firewall.helpers.extract_strings_from_user_input import (
    extract_strings_from_user_input_cached,
)
from aikido_firewall.helpers.logging import logger
from aikido_firewall.context import UINPUT_SOURCES as SOURCES
from .detect_shell_injection import detect_shell_injection


def check_context_for_shell_injection(command, operation, context):
    """
    This will check the context of the request for Shell injections
    """
    if not isinstance(command, str):
        # Command must be string to run algorithm
        return {}
    for source in SOURCES:
        if hasattr(context, source):
            user_inputs = extract_strings_from_user_input_cached(
                getattr(context, source), source
            )
            for user_input, path in user_inputs.items():
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
