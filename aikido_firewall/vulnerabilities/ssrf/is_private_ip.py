"""Only exports is_private_ip function"""

import ipaddress

# Define private IP ranges
PRIVATE_IP_RANGES = [
    "0.0.0.0/8",
    "10.0.0.0/8",
    "100.64.0.0/10",
    "127.0.0.0/8",
    "169.254.0.0/16",
    "172.16.0.0/12",
    "192.0.0.0/24",
    "192.0.2.0/24",
    "192.31.196.0/24",
    "192.52.193.0/24",
    "192.88.99.0/24",
    "192.168.0.0/16",
    "192.175.48.0/24",
    "198.18.0.0/15",
    "198.51.100.0/24",
    "203.0.113.0/24",
    "240.0.0.0/4",
    "224.0.0.0/4",
    "255.255.255.255/32",
]

PRIVATE_IPV6_RANGES = [
    "::/128",  # Unspecified address
    "::1/128",  # Loopback address
    "fc00::/7",  # Unique local address (ULA)
    "fe80::/10",  # Link-local address (LLA)
    "::ffff:127.0.0.1/128",  # IPv4-mapped address
]

# Create a set to hold private IP networks
private_ip_networks = set()

# Add private IPv4 ranges to the set
for ip_range in PRIVATE_IP_RANGES:
    private_ip_networks.add(ipaddress.ip_network(ip_range))

# Add private IPv6 ranges to the set
for ip_range in PRIVATE_IPV6_RANGES:
    private_ip_networks.add(ipaddress.ip_network(ip_range))


def normalize_ip(ip):
    """Normalize the IP address by removing leading zeros."""
    if not ":" in ip:
        # Normalize IPv4 ip's
        parts = ip.split(".")
        normalized_parts = [
            str(int(part)) for part in parts
        ]  # Convert to int and back to str to remove leading zeros
        return ".".join(normalized_parts)
    return ip


def is_private_ip(ip):
    """Returns true if the ip entered is private"""
    try:
        normalized_ip = normalize_ip(ip)
        ip_obj = ipaddress.ip_address(normalized_ip)
        if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped:
            return any(ip_obj.ipv4_mapped in network for network in private_ip_networks)

        # Check if the IP address is in any of the private networks
        return any(ip_obj in network for network in private_ip_networks)
    except ValueError:
        return False  # Return False if the IP address is invalid
