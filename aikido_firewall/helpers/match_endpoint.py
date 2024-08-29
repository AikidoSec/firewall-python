"""
Helper function file, see function docstring
"""

import regex as re
from .try_parse_url_path import try_parse_url_path


def match_endpoint(route_metadata, endpoints, multi=False):
    """
    Based on the context's url this tries to find a match in the list of endpoints
    """
    if not route_metadata["method"]:
        return None

    possible = [
        endpoint
        for endpoint in endpoints
        if endpoint["method"] == "*" or endpoint["method"] == route_metadata["method"]
    ]
    results = []

    if not multi:
        endpoint = next(
            (
                endpoint
                for endpoint in possible
                if endpoint["route"] == route_metadata["route"]
            ),
            None,
        )

        if endpoint:
            return {"endpoint": endpoint, "route": endpoint["route"]}
    else:
        for endpoint in possible:
            if endpoint["route"] == route_metadata["route"]:
                results.append({"endpoint": endpoint, "route": endpoint["route"]})

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
            if not multi:
                return {"endpoint": wildcard, "route": route}
            results.append({"endpoint": wildcard, "route": route})
    if len(results) > 0:
        return results
    return None
