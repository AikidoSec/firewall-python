"""
Mainly exports function `find_hostname_in_context`
"""

from aikido_zen.helpers.extract_strings_from_context import extract_strings_from_context
from .find_hostname_in_userinput import find_hostname_in_userinput


def find_hostname_in_context(hostname, context, port):
    """Tries to locate the given hostname from context"""
    if not isinstance(hostname, str) or not isinstance(port, int):
        # Validate hostname and port input
        return None

    # Punycode detected in hostname, while user input may not be in Punycode
    # We need to convert it to ensure we compare the right values
    if "xn--" in hostname:
        try:
            hostname = hostname.encode("ascii").decode("idna")
        except Exception:
            # Seems to be a malformed Punycode sequence, retain original
            # hostname
            pass

    for user_input, path, source in extract_strings_from_context(context):
        found = find_hostname_in_userinput(user_input, hostname, port)
        if found:
            return {
                "source": source,
                "pathToPayload": path,
                "payload": user_input,
            }
