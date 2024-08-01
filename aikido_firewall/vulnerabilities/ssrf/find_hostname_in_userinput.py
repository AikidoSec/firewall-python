"""
Only exports find_hostname_in_userinput function
"""

from urllib.parse import urlparse
from aikido_firewall.helpers.get_port_from_url import get_port_from_url


def try_parse_url(url: str):
    """Tries to parse the url using urlparse"""
    try:
        parsed_url = urlparse(url)
        if parsed_url.scheme and parsed_url.netloc:
            return parsed_url
        return None
    except Exception:
        return None


def find_hostname_in_userinput(user_input, hostname, port=None):
    """
    Returns true if the hostname is in userinput
    """
    if len(user_input) <= 1:
        return False

    hostname_url = try_parse_url(f"http://{hostname}")
    print(hostname_url)
    if not hostname_url:
        return False

    variants = [user_input, f"http://{user_input}", f"https://{user_input}"]
    for variant in variants:
        user_input_url = try_parse_url(variant)
        if user_input_url and user_input_url.hostname == hostname_url.hostname:
            user_port = get_port_from_url(user_input_url.geturl())

            if port is None:
                return True
            if port is not None and user_port == port:
                return True

    return False
