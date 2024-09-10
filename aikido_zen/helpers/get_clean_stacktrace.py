"""Exports function `get_clean_stacktrace`"""

import inspect
import sys


def get_clean_stacktrace():
    """Returns a cleaned up stacktrace"""
    # Get the current stack
    stack = inspect.stack()

    # List of built-in modules to filter out
    ignored_modules = sys.builtin_module_names

    cleaned_stack = []

    for frame_info in stack:
        name = frame_info.frame.f_globals.get("__name__", "")

        if name not in ignored_modules and not name.startswith("aikido_zen"):
            cleaned_stack.append(
                f"File: {frame_info.filename}, L{frame_info.lineno} {frame_info.function}(...)"
            )

    cleaned_stack.reverse()
    return "• " + "\n\n• ".join(cleaned_stack)
