"""exports contains_private_ip_address"""

from aikido_firewall.helpers.try_parse_url import try_parse_url
from .is_private_ip import is_private_ip


def contains_private_ip_address(hostname):
    """
    Checks if the hostname contains an IP that's private
    """
    if hostname == "localhost":
        return True

    # Attempt to parse the URL
    url = try_parse_url(f"http://{hostname}")
    if url is None:
        return False

    # Check for IPv6 addresses enclosed in square brackets
    if url.hostname.startswith("[") and url.hostname.endswith("]"):
        ipv6 = url.hostname[1:-1]  # Extract the IPv6 address
        if is_private_ip(ipv6):
            return True

    return is_private_ip(url.hostname)
