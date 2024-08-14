"""
Mainly exports function `find_hostname_in_context`
"""

from aikido_firewall.context import UINPUT_SOURCES
from aikido_firewall.helpers.extract_strings_from_user_input import (
    extract_strings_from_user_input_cached,
)
from .find_hostname_in_userinput import find_hostname_in_userinput


def find_hostname_in_context(hostname, context, port):
    """Tries to locate the given hostname from context"""
    for source in UINPUT_SOURCES:
        if not hasattr(context, source):
            continue
        user_inputs = extract_strings_from_user_input_cached(
            getattr(context, source), source
        )
        if not user_inputs:
            continue
        for user_input, path in user_inputs.items():
            found = find_hostname_in_userinput(user_input, hostname, port)
            if found:
                return {
                    "source": source,
                    "pathToPayload": path,
                    "payload": user_input,
                }
