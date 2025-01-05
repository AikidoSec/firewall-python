"""Exports add_ip_address_to_blocklist"""

from aikido_zen.helpers.blocklist import get_ip_address_type


def add_ip_address_to_blocklist(ip: str, blocklist) -> bool:
    """Checks for CIDR, adds as ip, or subnet."""
    is_cidr = "/" in ip

    if not is_cidr:
        ip_type = get_ip_address_type(ip)
        if not ip_type:
            return False
        blocklist.add_address(ip, ip_type)
        return True

    plain_ip, range_str = ip.split("/")
    ip_type = get_ip_address_type(plain_ip)
    if not ip_type:
        return False

    try:
        ip_range = int(range_str)
    except ValueError:
        return False

    if ip_range < 1:
        return False

    if ip_range > 32 and ip_type == "ipv4":
        return False

    if ip_range > 128 and ip_type == "ipv6":
        return False

    blocklist.add_subnet(plain_ip, ip_range, ip_type)
    return True
