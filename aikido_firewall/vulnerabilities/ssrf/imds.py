"""
imds.py file, exports :
is_imds_ip_address, is_trusted_hostname
"""


class BlockList:
    """A list of IP's that shouldn't be accessed"""

    def __init__(self):
        self.blocked_addresses = {"ipv4": set(), "ipv6": set()}

    def add_address(self, address, address_type):
        """Add an address to this list"""
        if address_type in self.blocked_addresses:
            self.blocked_addresses[address_type].add(address)

    def check(self, address, address_type=None):
        """Check if the IP is on the list"""
        if address_type:
            return address in self.blocked_addresses.get(address_type, set())
        return any(
            address in addresses for addresses in self.blocked_addresses.values()
        )


# Create an instance of BlockList
imds_addresses = BlockList()

# Block the IP addresses used by AWS EC2 instances for IMDS
imds_addresses.add_address("169.254.169.254", "ipv4")
imds_addresses.add_address("fd00:ec2::254", "ipv6")


def is_imds_ip_address(ip):
    """Checks if the IP is an imds ip"""
    return imds_addresses.check(ip) or imds_addresses.check(ip, "ipv6")


# Trusted hostnames for Google Cloud
trusted_hosts = ["metadata.google.internal", "metadata.goog"]


def is_trusted_hostname(hostname):
    """Checks if this hostname is trusted"""
    return hostname in trusted_hosts
