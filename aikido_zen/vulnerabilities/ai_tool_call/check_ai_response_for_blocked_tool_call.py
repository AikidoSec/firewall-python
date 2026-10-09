"""
Exports `check_ai_response_for_blocked_tool_call`
"""

from aikido_zen.helpers.get_blocked_ai_tool_rules import get_blocked_ai_tool_rules
from .detect_blocked_ai_tool_call import (
    argument_matches_pattern,
    detect_blocked_ai_tool_call,
)
from .extract_tool_calls_from_ai_response import extract_tool_calls_from_ai_response


def check_ai_response_for_blocked_tool_call(response, operation):
    """
    Inspect an AI provider response for blocked tool calls.
    Returns an attack dict, or {} when nothing matches.
    """
    names, patterns = get_blocked_ai_tool_rules()
    if not names and not patterns:
        return {}

    for tool_name, arguments in extract_tool_calls_from_ai_response(response):
        if not detect_blocked_ai_tool_call(
            tool_name, arguments, names=names, patterns=patterns
        ):
            continue

        metadata = {"tool": tool_name}
        for pattern in patterns:
            if argument_matches_pattern(arguments, pattern):
                metadata["pattern"] = pattern
                break

        return {
            "operation": operation,
            "kind": "ai_tool_call",
            "source": "",
            "pathToPayload": "",
            "metadata": metadata,
            "payload": {"tool": tool_name, "arguments": arguments},
        }

    return {}
