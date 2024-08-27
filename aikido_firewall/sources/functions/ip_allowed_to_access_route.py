"""Exports `ip_allowed_to_access_route`"""

from aikido_firewall.helpers.is_localhost_ip import is_localhost_ip


def ip_allowed_to_access_route(remote_address, route_metadata, connection_manager):
    """
    Checks if the ip address can access the route, given the service conf
    """
    ip = remote_address
    if ip and is_localhost_ip(ip):
        return True

    matches = connection_manager.conf.get_endpoints(route_metadata)
    if not matches:
        return True

    for endpoint in matches:
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
