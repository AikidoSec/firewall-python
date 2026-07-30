"""
Helper function file, see function docstring
"""

import os


def get_blocked_ai_tool_rules():
    """
    Reads AIKIDO_BLOCKED_AI_TOOL_NAMES and AIKIDO_BLOCKED_AI_TOOL_ARG_PATTERNS.
    Returns (tool_names: set[str], arg_patterns: list[str]).
    """
    names_raw = os.getenv("AIKIDO_BLOCKED_AI_TOOL_NAMES", "")
    patterns_raw = os.getenv("AIKIDO_BLOCKED_AI_TOOL_ARG_PATTERNS", "")

    names = {part.strip() for part in names_raw.split(",") if part.strip()}
    patterns = [part.strip() for part in patterns_raw.split(",") if part.strip()]
    return names, patterns
