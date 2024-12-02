"""Exports blocklist class and get_ip_address_type"""

import ipaddress


def get_ip_address_type(ip):
    """Returns type, ipv4 or ipv6"""
    try:
        if ipaddress.ip_address(ip).version == 4:
            return "ipv4"
        elif ipaddress.ip_address(ip).version == 6:
            return "ipv6"
    except ValueError:
        return None


class BlockList:
    """A blocklist, where you can add subnets and addresses"""

    def __init__(self):
        self.blocked_addresses = set()
        self.blocked_subnets = []

    def add_address(self, ip: str, ip_type: str):
        self.blocked_addresses.add((ip, ip_type))

    def add_subnet(self, plain_ip: str, ip_range: int, ip_type: str):
        self.blocked_subnets.append((plain_ip, ip_range, ip_type))

    def is_blocked(self, ip: str) -> bool:
        ip_type = get_ip_address_type(ip)
        if not ip_type:
            return False

        # Check if the IP address is in the blocked addresses
        if (ip, ip_type) in self.blocked_addresses:
            return True

        # Check if the IP address is in any of the blocked subnets
        ip_addr = ipaddress.ip_address(ip)
        for plain_ip, ip_range, _ in self.blocked_subnets:
            subnet = ipaddress.ip_network(f"{plain_ip}/{ip_range}", strict=False)
            if ip_addr in subnet:
                return True

        return False
