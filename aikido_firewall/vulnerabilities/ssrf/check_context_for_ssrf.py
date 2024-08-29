"""Exports check_context_for_ssrf"""

from aikido_firewall.helpers.extract_strings_from_user_input import (
    extract_strings_from_user_input_cached,
)
from aikido_firewall.helpers.logging import logger
from aikido_firewall.context import UINPUT_SOURCES as SOURCES
from .find_hostname_in_userinput import find_hostname_in_userinput
from .contains_private_ip_address import contains_private_ip_address


def check_context_for_ssrf(hostname, port, operation, context):
    """
    This will check the context for SSRF
    """
    if not isinstance(hostname, str) or not isinstance(port, int):
        # Validate hostname and port input
        return {}
    for source in SOURCES:
        if hasattr(context, source):
            user_inputs = extract_strings_from_user_input_cached(
                getattr(context, source), source
            )
            for user_input, path in user_inputs.items():
                found = find_hostname_in_userinput(user_input, hostname, port)
                if found and contains_private_ip_address(hostname):
                    return {
                        "operation": operation,
                        "kind": "ssrf",
                        "source": source,
                        "pathToPayload": path,
                        "metadata": {"hostname": hostname},
                        "payload": user_input,
                    }
    return {}
