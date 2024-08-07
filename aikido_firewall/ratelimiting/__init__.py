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
    route = match["route"]
    if not endpoint["rateLimiting"] or not endpoint["rateLimiting"]["enabled"]:
        return {"block": False}

    # Production logic, still missing

    if context.remote_address:
        max_requests = int(endpoint["rateLimiting"]["maxRequests"])
        windows_size_in_ms = int(endpoint["rateLimiting"]["windowSizeInMS"])
        allowed = reporter.rate_limiter.is_allowed(
            f"{context.method}:{route}:ip:{context.remote_address}",
            windows_size_in_ms,
            max_requests,
        )
        if not allowed:
            return {"block": True, "trigger": "ip"}

    return {"block": False}
