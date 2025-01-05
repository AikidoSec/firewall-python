"""
Aikido can rate limit urls, IPs, Users
"""

from .get_ratelimited_endpoint import get_ratelimited_endpoint


def should_ratelimit_request(route_metadata, remote_address, user, connection_manager):
    """
    Checks if the request should be ratelimited or not
    route_metadata object includes route, url and method
    """
    endpoints = connection_manager.conf.get_endpoints(route_metadata)
    endpoint = get_ratelimited_endpoint(endpoints, route_metadata["route"])
    if not endpoint:
        return {"block": False}

    max_requests = int(endpoint["rateLimiting"]["maxRequests"])
    windows_size_in_ms = int(endpoint["rateLimiting"]["windowSizeInMS"])
    is_bypassed_ip = connection_manager.conf.is_bypassed_ip(remote_address)

    if is_bypassed_ip:
        return {"block": False}
    if user:
        uid = user["id"]
        method = endpoint.get("method")
        route = endpoint.get("route")

        allowed = connection_manager.rate_limiter.is_allowed(
            f"{method}:{route}:user:{uid}",
            windows_size_in_ms,
            max_requests,
        )
        if not allowed:
            return {"block": True, "trigger": "user"}
        # Do not check IP rate limit if user is set
        return {"block": False}

    if remote_address:
        method = endpoint.get("method")
        route = endpoint.get("route")

        allowed = connection_manager.rate_limiter.is_allowed(
            f"{method}:{route}:ip:{remote_address}",
            windows_size_in_ms,
            max_requests,
        )
        if not allowed:
            return {"block": True, "trigger": "ip"}

    return {"block": False}
