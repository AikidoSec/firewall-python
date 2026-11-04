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

    if user and connection_manager.conf.is_user_excluded_from_rate_limiting(user["id"]):
        return {"block": False}

    max_requests = int(endpoint["rateLimiting"]["maxRequests"])
    windows_size_in_ms = int(endpoint["rateLimiting"]["windowSizeInMS"])

    # Only one key is checked: a group over the user, the user over the IP.
    if group:
        key, trigger = get_key_for_group(endpoint, group), "group"
    elif user:
        key, trigger = get_key_for_user(endpoint, user), "user"
    elif remote_address:
        key, trigger = get_key_for_ip(endpoint, remote_address), "ip"
    else:
        return {"block": False}

    result = connection_manager.rate_limiter.record_request(
        key, windows_size_in_ms, max_requests
    )
    if result["allowed"]:
        return {"block": False}
    return {
        "block": True,
        "trigger": trigger,
        "retry_after_seconds": result["retry_after_seconds"],
    }


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
