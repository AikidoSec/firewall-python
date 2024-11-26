"""Exports extract_strings_from_context function"""

from aikido_zen.context import UINPUT_SOURCES as SOURCES
from .extract_strings_from_user_input import extract_strings_from_user_input_cached


def extract_strings_from_context(context):
    """
    Iterates over all sources and generates array :
    [(userinput, path, source), ...]
    """
    results = []
    for source in SOURCES:
        if hasattr(context, source):
            user_inputs = extract_strings_from_user_input_cached(
                getattr(context, source), source
            )
            for user_input, path in user_inputs.items():
                if user_input is not None and path is not None:
                    results.append((user_input, path, source))
    return results
