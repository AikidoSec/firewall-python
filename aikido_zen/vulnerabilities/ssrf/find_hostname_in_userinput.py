"""
Only exports find_hostname_in_userinput function
"""

from typing import Optional, List

from aikido_zen.helpers.get_port_from_url import get_port_from_url
from aikido_zen.helpers.try_parse_url import try_parse_url
from aikido_zen.vulnerabilities.ssrf.normalize_string_to_hostname_and_port import (
    normalize_string_to_hostname_and_port,
)


def find_hostname_in_userinput(
    user_input: str, hostname_variants: List[str], port: Optional[int] = None
):
    """
    Returns true if the hostname is in userinput
    """
    if len(user_input) <= 1:
        return False

    user_input_variants = normalize_string_to_hostname_and_port(user_input)

    for user_input_hostname, user_input_port in user_input_variants:
        if user_input_hostname in hostname_variants:
            # We were unable to retrieve the port from the URL, likely because it contains an invalid port.
            # Let's assume we have found the hostname in the user input, even though it doesn't match on port.
            # See: https://github.com/AikidoSec/firewall-python/pull/180.
            if user_input_port is None:
                return True

            if port is None:
                return True
            if port is not None and user_input_port == port:
                return True

    return False
