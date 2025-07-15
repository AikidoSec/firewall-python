"""
Only exports find_hostname_in_userinput function
"""

from typing import List

from aikido_zen.helpers.get_port_from_url import get_port_from_url
from aikido_zen.helpers.try_parse_url import try_parse_url


def find_hostname_in_userinput(user_input, hostname, port=None):
    """
    Returns true if the hostname is in userinput
    """
    if len(user_input) <= 1:
        return False

    hostname_options = get_hostname_options(hostname)
    if len(hostname_options) == 0:
        return False

    variants = [user_input, f"http://{user_input}", f"https://{user_input}"]
    for variant in variants:
        user_input_url = try_parse_url(variant)
        if user_input_url and user_input_url.hostname in hostname_options:
            user_port = get_port_from_url(user_input_url.geturl())

            # We were unable to retrieve the port from the URL, likely because it contains an invalid port.
            # Let's assume we have found the hostname in the user input, even though it doesn't match on port.
            # See: https://github.com/AikidoSec/firewall-python/pull/180.
            if user_port is None:
                return True

            if port is None:
                return True
            if port is not None and user_port == port:
                return True

    return False


def get_hostname_options(raw_hostname: str) -> List[str]:
    options_urls = [try_parse_url(f"http://{raw_hostname}")]

    # Add a case for hostnames like ::1 or ::ffff:127.0.0.1, who need brackets to be parsed
    options_urls.append(try_parse_url(f"http://[{raw_hostname}]"))

    # Add a case when the hostname is in punycode (like xn--pp-oia.aikido.dev)
    if "xn--" in raw_hostname:
        hostname_decoded = raw_hostname.encode("ascii", errors="").decode("idna")
        options_urls.append(try_parse_url(f"http://{hostname_decoded}"))

    # Map to url.hostname
    options = []
    for options_url in options_urls:
        if options_url and options_url.hostname:
            options.append(options_url.hostname)
    return options
