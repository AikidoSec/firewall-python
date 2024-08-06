"""
Helper function file, see function docstring
"""

import regex as re
from .try_parse_url_path import try_parse_url_path


def match_endpoint(context, endpoints):
    """
    Based on the context's url this tries to find a match in the list of endpoints
    """
    if not context.method:
        return None

    possible = [
        endpoint
        for endpoint in endpoints
        if endpoint["method"] == "*" or endpoint["method"] == context.method
    ]

    endpoint = next(
        (endpoint for endpoint in possible if endpoint["route"] == context.route), None
    )

    if endpoint:
        return {"endpoint": endpoint, "route": endpoint["route"]}

    if not context.url:
        return None

    path = try_parse_url_path(context.url)

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
            return {"endpoint": wildcard, "route": route}

    return None
