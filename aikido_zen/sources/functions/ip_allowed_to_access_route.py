"""Exports `ip_allowed_to_access_route`"""

from aikido_zen.helpers.ip_matcher import IPMatcher
from aikido_zen.helpers.is_localhost_ip import is_localhost_ip


def ip_allowed_to_access_route(remote_address, route_metadata, endpoints):
    """
    Checks if the ip address can access the route, given the service conf
    """
    ip = remote_address
    if ip and is_localhost_ip(ip):
        return True

    if not endpoints:
        return True

    for endpoint in endpoints:
        allowed_ips: IPMatcher = endpoint.get("allowedIPAddresses", None)
        if not allowed_ips or not isinstance(allowed_ips, IPMatcher):
            # Feature might not be supported
            continue
        if not ip:
            # We only check it here because if allowedIPAddresses isn't set
            # We don't want to change any default behaviour
            return False
        if not allowed_ips.has(ip):
            # The IP is not in the allowlist, so block
            return False
    return True
