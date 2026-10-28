"""
Mainly exports function `find_hostname_in_context`
"""

from aikido_zen.helpers.extract_strings_from_context import extract_strings_from_context
from .find_hostname_in_userinput import find_hostname_in_userinput
from .get_hostname_options import get_hostname_options
from .is_request_to_itself import is_request_to_itself
from ...context import Context


def find_hostname_in_context(hostname, context: Context, port):
    """Tries to locate the given hostname from context"""
    if not isinstance(hostname, str) or not isinstance(port, int):
        # Validate hostname and port input
        return None

    # We don't want to block outgoing requests to hostnames the operator has
    # declared as their own server via AIKIDO_TRUSTED_HOSTNAMES.
    if is_request_to_itself(hostname):
        return None

    # Gets the different hostname options: with/without punycode, with/without brackets for IPv6
    hostname_options = get_hostname_options(hostname)

    for user_input, path, source in extract_strings_from_context(context):
        found = find_hostname_in_userinput(user_input, hostname_options, port)
        if found:
            return {
                "source": source,
                "pathToPayload": path,
                "payload": user_input,
            }
