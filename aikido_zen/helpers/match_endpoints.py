"""
Helper function file, see function docstring
"""

import regex as re
from .try_parse_url_path import try_parse_url_path


def match_endpoints(route_metadata, endpoints):
    """
    Based on the context's url this tries to find a match in the list of endpoints
    """
    if not route_metadata["method"]:
        return None

    possible = []
    i = 0
    for endpoint in endpoints:
        if endpoint["method"] == route_metadata["method"]:
            possible.insert(i, endpoint)  # Add match to first part of array
            i += 1
        elif endpoint["method"] == "*":
            possible.append(endpoint)

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
        route = wildcard["route"]
        regex = re.compile(f"^{route.replace('*', '(.*)')}\/?$", re.IGNORECASE)

        if regex.match(path):
            results.append(wildcard)
    if len(results) > 0:
        return results
    return None
