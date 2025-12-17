"""
imds.py file, exports :
is_imds_ip_address, is_trusted_hostname, resolves_to_imds_ip
"""

from aikido_zen.helpers.ip_matcher import IPMatcher
from aikido_zen.helpers.ip_matcher.map_ipv4_to_ipv6 import map_ipv4_to_ipv6

imds_addresses = IPMatcher()

# Block the IP addresses used by AWS EC2 instances for IMDS
imds_addresses.add("169.254.169.254")
imds_addresses.add("fd00:ec2::254")
imds_addresses.add(map_ipv4_to_ipv6("169.254.169.254"))

# Block the IP address used by Alibaba Cloud
imds_addresses.add("100.100.100.200")
imds_addresses.add(map_ipv4_to_ipv6("100.100.100.200"))


def is_imds_ip_address(ip):
    """Checks if the IP is an imds ip"""
    return imds_addresses.has(ip)


# Trusted hostnames for Google Cloud
trusted_hosts = ["metadata.google.internal", "metadata.goog"]


def is_trusted_hostname(hostname):
    # Stored SSRF attacks happen when an attacker can alter how hostnames are resolved by
    # e.g. having inserted an entry in /etc/hosts, or having spoofed the DNS

    # If the hostname is an ip itself, no resolving happens. We can safely ignore this, it's not an attack.
    if imds_addresses.has(hostname):
        # hostname comes from user input, then I guess they just inputted IMDS ip, could be malicious
        return True

    # If the hostname is a trusted host (like metadata.goog), there was no spoofing of hostnames, so it's not an attack
    if hostname in trusted_hosts:
        return True

    return False


def resolves_to_imds_ip(resolved_ip_addresses, hostname):
    """
    Returns the IMDS IP address as a string if it exists in resolved_ip_addresses, otherwise returns None
    """
    if is_trusted_hostname(hostname):
        return None
    for ip in resolved_ip_addresses:
        if is_imds_ip_address(ip):
            return ip
    return None
