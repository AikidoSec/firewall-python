"""Exports function `get_clean_stacktrace`"""

import traceback


def get_clean_stacktrace():
    """Returns a cleaned up stacktrace"""
    stack_trace = traceback.extract_stack()
    filtered_stack_trace = filter(filter_no_aikido, stack_trace)

    formatted_trace = "".join(traceback.format_list(filtered_stack_trace))
    return formatted_trace


def filter_no_aikido(frame):
    """Custom filter to remove aikido frames"""
    return "/site-packages/aikido_firewall/" not in frame.filename
