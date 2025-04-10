"""Exports `ip_allowed_to_access_route`"""

from aikido_zen.helpers.is_localhost_ip import is_localhost_ip
from aikido_zen.helpers.iplist import IPList


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
        if not isinstance(endpoint["allowedIPAddresses"], IPList):
            #  We will continue to check all the other matches
            continue
        if not ip:
            # We only check it here because if allowedIPAddresses isn't set
            # We don't want to change any default behaviour
            return False
        if not endpoint["allowedIPAddresses"].matches(ip):
            # The IP is not in the allowlist, so block
            return False
    return True
