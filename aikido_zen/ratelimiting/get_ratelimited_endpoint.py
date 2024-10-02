"""Exports get_ratelimited_endpoint, see function docstring"""


def get_ratelimited_endpoint(endpoints, route):
    """
    Filters through endpoints, tries to find an exact match otherwise tries to find the
    endpoint with the least amount of allowed requests.
    """
    if not endpoints:
        return None
    matches = []
    for endpoint in endpoints:
        if (
            endpoint.get("rateLimiting")
            and endpoint["rateLimiting"].get("enabled") is True
        ):
            if endpoint.get("route") == route:
                # Exact match, return the exact match
                return endpoint
            matches.append(endpoint)

    if len(matches) <= 0:
        return None

    matches.sort(key=get_endpoint_ratelimiting_rate)

    return matches[0]


def get_endpoint_ratelimiting_rate(endpoint):
    """
    Returns the rate at which a route gets ratelimited (max requests / ms)
    """
    max_reqs = endpoint["rateLimiting"].get("maxRequests")
    window_ms = endpoint["rateLimiting"].get("windowSizeInMS")
    return max_reqs / window_ms
