"""
Aikido can rate limit urls, IPs, Users
"""

from .get_ratelimited_endpoint import get_ratelimited_endpoint


def should_ratelimit_request(
    route_metadata, remote_address, user, connection_manager, group=None
):
    """
    Checks if the request should be rate-limited or not (checks user, group id & ip)
    route_metadata object includes route, url and method
    """
    endpoints = connection_manager.conf.get_endpoints(route_metadata)
    endpoint = get_ratelimited_endpoint(endpoints, route_metadata["route"])
    if not endpoint:
        return {"block": False}

    is_bypassed_ip = connection_manager.conf.is_bypassed_ip(remote_address)
    if is_bypassed_ip:
        return {"block": False}

    max_requests = int(endpoint["rateLimiting"]["maxRequests"])
    windows_size_in_ms = int(endpoint["rateLimiting"]["windowSizeInMS"])

    if group:
        allowed = connection_manager.rate_limiter.is_allowed(
            get_key_for_group(endpoint, group),
            windows_size_in_ms,
            max_requests,
        )
        if not allowed:
            return {"block": True, "trigger": "group"}

        # Do not check IP or user rate limit if group is set
        return {"block": False}
    if user:
        allowed = connection_manager.rate_limiter.is_allowed(
            get_key_for_user(endpoint, user),
            windows_size_in_ms,
            max_requests,
        )
        if not allowed:
            return {"block": True, "trigger": "user"}
        # Do not check IP rate limit if user is set
        return {"block": False}
    if remote_address:
        allowed = connection_manager.rate_limiter.is_allowed(
            get_key_for_ip(endpoint, remote_address),
            windows_size_in_ms,
            max_requests,
        )
        if not allowed:
            return {"block": True, "trigger": "ip"}

    return {"block": False}


def get_key_for_group(endpoint, group_id):
    method, route = endpoint.get("method"), endpoint.get("route")
    return f"{method}:{route}:group:{group_id}"


def get_key_for_user(endpoint, user):
    method, route = endpoint.get("method"), endpoint.get("route")
    user_id = user.get("id")
    return f"{method}:{route}:user:{user_id}"


def get_key_for_ip(endpoint, remote_address):
    method, route = endpoint.get("method"), endpoint.get("route")
    return f"{method}:{route}:ip:{remote_address}"
