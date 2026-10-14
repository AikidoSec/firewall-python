"""
Exports `detect_blocked_ai_tool_call`
"""

import json
from pathlib import PurePosixPath

from aikido_zen.helpers.get_blocked_ai_tool_rules import get_blocked_ai_tool_rules


def _argument_values(arguments):
    if arguments is None:
        return []
    if isinstance(arguments, str):
        values = [arguments]
        try:
            arguments = json.loads(arguments)
        except (json.JSONDecodeError, TypeError):
            return values
    else:
        values = []

    def walk(node):
        if isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
        elif node is not None:
            values.append(str(node))

    if isinstance(arguments, (dict, list)):
        walk(arguments)
    elif not values:
        values.append(str(arguments))
    return values


def argument_matches_pattern(arguments, pattern):
    """True if any tool argument value matches the glob pattern."""
    for value in _argument_values(arguments):
        normalized = value.replace("\\", "/").lstrip("/")
        try:
            if PurePosixPath(normalized).match(pattern):
                return True
        except ValueError:
            continue
    return False


def detect_blocked_ai_tool_call(tool_name, arguments, names=None, patterns=None):
    """
    Detects if a tool call matches the configured block rules.
    """
    if names is None or patterns is None:
        env_names, env_patterns = get_blocked_ai_tool_rules()
        if names is None:
            names = env_names
        if patterns is None:
            patterns = env_patterns

    if not names and not patterns:
        return False
    if names and tool_name not in names:
        return False
    if not patterns:
        return True

    return any(
        argument_matches_pattern(arguments, pattern) for pattern in patterns
    )
