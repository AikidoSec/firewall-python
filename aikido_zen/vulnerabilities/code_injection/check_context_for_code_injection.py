"""
This will check the context for code injection
"""

from aikido_zen.helpers.extract_strings_from_user_input import (
    extract_strings_from_user_input_cached,
)
from aikido_zen.helpers.logging import logger
from aikido_zen.context import UINPUT_SOURCES as SOURCES
from .detect_code_injection import detect_code_injection


def check_context_for_code_injection(statement, operation, context):
    """
    This will check the context of the request for Shell injections
    """
    if not isinstance(statement, str):
        # Statement must be string to run algorithm
        return {}
    for source in SOURCES:
        if hasattr(context, source):
            user_inputs = extract_strings_from_user_input_cached(
                getattr(context, source), source
            )
            for user_input, path in user_inputs.items():
                if detect_code_injection(statement, user_input):
                    return {
                        "operation": operation,
                        "kind": "code_injection",
                        "source": source,
                        "pathToPayload": path,
                        "metadata": {"statement": statement},
                        "payload": user_input,
                    }
    return {}
