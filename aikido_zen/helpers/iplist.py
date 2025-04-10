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


class IPList:
    """A blocklist, where you can add subnets and addresses"""

    def __init__(self, ip_list=None):
        """Initializes the IPList, optionally with a list of IPs or CIDRs"""
        self.blocked_addresses = set()
        self.blocked_subnets = []

        if ip_list:
            for ip_or_cidr in ip_list:
                self.add(ip_or_cidr)

    def add_address(self, ip: str, ip_type: str):
        self.blocked_addresses.add((ip, ip_type))

    def add_subnet(self, plain_ip: str, ip_range: int, ip_type: str):
        self.blocked_subnets.append((plain_ip, ip_range, ip_type))

    def add(self, ip_or_cidr):
        """
        Checks whether ip_or_cidr is an IP address or is a subnet, and decides the correct IP type (IPv4 or IPv6)
        """
        if "/" not in ip_or_cidr:  # IP Address
            ip_type = get_ip_address_type(ip_or_cidr)
            if ip_type:
                self.add_address(ip_or_cidr, ip_type)
        else:  # Subnet
            plain_ip, range_str = ip_or_cidr.split("/")
            try:
                ip_range = int(range_str)
            except ValueError:
                return
            ip_type = get_ip_address_type(plain_ip)
            if not ip_type:
                return

            self.add_subnet(plain_ip, ip_range, ip_type)

    def matches(self, ip: str) -> bool:
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
