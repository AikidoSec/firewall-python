"""
Only exports find_hostname_in_userinput function
"""

from typing import Optional, List, Tuple

from aikido_zen.helpers.get_port_from_url import get_port_from_url
from aikido_zen.helpers.try_parse_url import try_parse_url


def find_hostname_in_userinput(
    user_input: str, normalized_hostname: str, port: Optional[int] = None
):
    """
    Returns true if the hostname is in userinput
    """
    normalized_hostname = normalized_hostname.lower()
    if len(user_input) <= 1:
        return False

    user_input_variants = [user_input, f"http://{user_input}", f"https://{user_input}"]
    user_input_normalized_variants = normalize_raw_url_variants(user_input_variants)

    for user_input_hostname, user_input_port in user_input_normalized_variants:
        hostname_variants = [normalized_hostname, f"[{normalized_hostname}]"]
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


def normalize_raw_url_variants(
    url_variants: List[str],
) -> List[Tuple[str, Optional[int]]]:
    normalized_variants = []
    for variant in url_variants:
        # Try parse the variant as an url,
        user_input_url = try_parse_url(variant)
        if not user_input_url or not user_input_url.hostname:
            continue
        port = get_port_from_url(user_input_url.geturl())
        normalized_variants.append((user_input_url.hostname.lower(), port))
    return normalized_variants
