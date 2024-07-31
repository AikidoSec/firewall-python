"""
Aikido can rate limit urls, IPs, Users
"""


def should_ratelimit_request(context, reporter):
    """
    Checks if the request should be ratelimited or not
    """
    match = reporter.conf.get_endpoint(context)
    if not match:
        return {"block": False}
    endpoint = match["endpoint"]
    route = match.get["route"]
    if not endpoint["rateLimiting"] or not endpoint["rateLimiting"]["enabled"]:
        return {"block": False}

    # Production logic, still missing

    max_requests = int(endpoint["rateLimiting"]["maxRequests"])
    windows_size_in_ms = int(endpoint["rateLimiting"]["windowSizeInMS"])

    return {"block": False}
