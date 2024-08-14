"""
Aikido can rate limit urls, IPs, Users
"""


def should_ratelimit_request(context_metadata, remote_address, user, reporter):
    """
    Checks if the request should be ratelimited or not
    context_metadata object includes route, url and method
    """
    match = reporter.conf.get_endpoint(context_metadata)
    if not match:
        return {"block": False}
    endpoint = match["endpoint"]
    route = match["route"]
    if not endpoint["rateLimiting"] or not endpoint["rateLimiting"]["enabled"]:
        return {"block": False}

    # Production logic, still missing
    is_bypassed_ip = reporter.conf.is_bypassed_ip(remote_address)
    max_requests = int(endpoint["rateLimiting"]["maxRequests"])
    windows_size_in_ms = int(endpoint["rateLimiting"]["windowSizeInMS"])
    if remote_address and not is_bypassed_ip:
        method = context_metadata["method"]
        allowed = reporter.rate_limiter.is_allowed(
            f"{method}:{route}:ip:{remote_address}",
            windows_size_in_ms,
            max_requests,
        )
        if not allowed:
            return {"block": True, "trigger": "ip"}
    if user:
        uid = user["id"]
        method = context_metadata["method"]

        allowed = reporter.rate_limiter.is_allowed(
            f"{method}:{route}:user:{uid}",
            windows_size_in_ms,
            max_requests,
        )
        if not allowed:
            return {"block": True, "trigger": "user"}
    return {"block": False}
