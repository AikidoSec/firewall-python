from aikido_zen.helpers.is_localhost_ip import is_localhost_ip
from aikido_zen.vulnerabilities.ssrf.is_private_ip import is_private_ip


def is_ip_allowed_by_allowlist(service_config, ip):
    """
    This function was separated from the ServiceConfig object, because otherwise you would have a circular dep.
    """
    if not service_config.allowed_ips or len(service_config.allowed_ips) < 1:
        return True
    # Always allow access from local IP addresses
    if is_private_ip(ip):
        return True

    for entry in service_config.allowed_ips:
        if entry["iplist"].matches(ip):
            # If the IP matches one of the lists the IP is allowed :
            return True
    return False
