"""
Helper function file, see function docstring
"""

from functools import lru_cache

import regex as re
from aikido_zen.helpers.logging import logger
from .try_parse_url_path import try_parse_url_path


@lru_cache
def compile_wildcard_route(route):
    try:
        return re.compile(f"^{route.replace('*', '(.*)')}/?$", re.IGNORECASE)
    except re.error as e:
        # Raising here would turn off protection for every request.
        logger.warning("Route regex is not compiling: %s (%s)", route, e)
        return None


def match_endpoints(route_metadata, endpoints):
    """
    Based on the context's url this tries to find a match in the list of endpoints
    """
    if not route_metadata["method"]:
        return None

    exact_method_match = []
    possible = []
    for endpoint in endpoints:
        if endpoint["method"] == route_metadata["method"]:
            exact_method_match.append(endpoint)
        elif endpoint["method"] == "*":
            possible.append(endpoint)
    # Make sure the exact matches come first:
    possible = exact_method_match + possible

    results = []

    for endpoint in possible:
        if endpoint["route"] == route_metadata["route"]:
            results.append(endpoint)

    if not route_metadata["url"]:
        return None

    path = try_parse_url_path(route_metadata["url"])

    if not path:
        return None

    wildcards = sorted(
        (endpoint for endpoint in possible if "*" in endpoint["route"]),
        key=lambda e: e["route"].count("*"),
        reverse=True,
    )

    for wildcard in wildcards:
        regex = compile_wildcard_route(wildcard["route"])
        if regex and regex.match(path):
            results.append(wildcard)
    if len(results) > 0:
        return results
    return None
