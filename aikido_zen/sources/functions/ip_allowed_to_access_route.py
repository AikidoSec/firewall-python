"""Exports `ip_allowed_to_access_route`"""

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
        if not "allowedIPAddresses" in endpoint:
            #  This feature is not supported by the current aikido server version
            continue
        if not isinstance(endpoint["allowedIPAddresses"], list):
            #  We will continue to check all the other matches
            continue
        if len(endpoint["allowedIPAddresses"]) == 0:
            #  We will continue to check all the other matches
            continue
        if not ip:
            # We only check it here because if allowedIPAddresses isn't set
            # We don't want to change any default behaviour
            return False
        if not ip in endpoint["allowedIPAddresses"]:
            # The IP is not in the allowlist, so block
            return False
    return True
