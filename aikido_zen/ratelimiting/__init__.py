"""
Aikido can rate limit urls, IPs, Users
"""


def should_ratelimit_request(route_metadata, remote_address, user, connection_manager):
    """
    Checks if the request should be ratelimited or not
    route_metadata object includes route, url and method
    """
    match = connection_manager.conf.get_endpoint(route_metadata)
    if not match:
        return {"block": False}
    endpoint = match["endpoint"]
    route = match["route"]
    if not endpoint["rateLimiting"] or not endpoint["rateLimiting"]["enabled"]:
        return {"block": False}

    # Production logic, still missing
    is_bypassed_ip = connection_manager.conf.is_bypassed_ip(remote_address)
    max_requests = int(endpoint["rateLimiting"]["maxRequests"])
    windows_size_in_ms = int(endpoint["rateLimiting"]["windowSizeInMS"])
    if remote_address and not is_bypassed_ip:
        method = route_metadata["method"]
        allowed = connection_manager.rate_limiter.is_allowed(
            f"{method}:{route}:ip:{remote_address}",
            windows_size_in_ms,
            max_requests,
        )
        if not allowed:
            return {"block": True, "trigger": "ip"}
    if user:
        uid = user["id"]
        method = route_metadata["method"]

        allowed = connection_manager.rate_limiter.is_allowed(
            f"{method}:{route}:user:{uid}",
            windows_size_in_ms,
            max_requests,
        )
        if not allowed:
            return {"block": True, "trigger": "user"}
    return {"block": False}
