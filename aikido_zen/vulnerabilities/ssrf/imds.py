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
    """
    If the hostname is a trusted host (like metadata.goog), there was no spoofing of hostnames, so it's not an attack
    """
    return hostname in trusted_hosts


def resolves_to_imds_ip(resolved_ip_addresses, hostname):
    # Stored SSRF attacks happen when an attacker can alter how hostnames are resolved by
    # e.g. having inserted an entry in /etc/hosts, or having spoofed the DNS

    if is_trusted_hostname(hostname):
        return None
    for ip in resolved_ip_addresses:
        # Python also runs the DNS resolving function with IP addresses, since there is no resolving happening here
        # do not mark it as a stored ssrf attack
        if hostname.strip() == ip.strip():
            continue
        if is_imds_ip_address(ip):
            return ip
    return None
