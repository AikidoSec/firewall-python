"""
Module with logic to build a route, i.e. find route params
from a simple URL string
"""

import re
import ipaddress
from aikido_zen.helpers.looks_like_a_secret import looks_like_a_secret
from aikido_zen.helpers.try_parse_url_path import try_parse_url_path

UUID_REGEX = re.compile(
    r"(?:[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}|00000000-0000-0000-0000-000000000000|ffffffff-ffff-ffff-ffff-ffffffffffff)$",
    re.I,
)
NUMBER_REGEX = re.compile(r"^\d+$")
DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}|\d{2}-\d{2}-\d{4}$")
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)
HASH_REGEX = re.compile(
    r"^(?:[a-f0-9]{32}|[a-f0-9]{40}|[a-f0-9]{64}|[a-f0-9]{128})$", re.I
)
HASH_LENGTHS = [32, 40, 64, 128]


def build_route_from_url(url):
    """
    Main helper function which will build the route
    from a URL string as input
    """
    path = try_parse_url_path(url)

    if not path:
        return None

    route = "/".join(
        [replace_url_segment_with_param(segment) for segment in path.split("/")]
    )

    if route == "/":
        return "/"

    if route.endswith("/"):
        return route[:-1]

    return route


def replace_url_segment_with_param(segment):
    """
    ??????????
    """
    if not segment:  # Check if segment is empty
        return segment  # Return the segment as is if it's empty
    char_code = ord(segment[0])
    starts_with_number = 48 <= char_code <= 57  # ASCII codes for '0' to '9'

    if starts_with_number and NUMBER_REGEX.match(segment):
        return ":number"

    if len(segment) == 36 and UUID_REGEX.match(segment):
        return ":uuid"

    if starts_with_number and DATE_REGEX.match(segment):
        return ":date"

    if "@" in segment and EMAIL_REGEX.match(segment):
        return ":email"

    try:
        ipaddress.ip_address(segment)
        return ":ip"
    except ValueError:
        pass

    if len(segment) in HASH_LENGTHS and HASH_REGEX.match(segment):
        return ":hash"

    if looks_like_a_secret(segment):
        return ":secret"

    return segment
