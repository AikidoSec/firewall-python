def map_ipv4_to_ipv6(ip: str) -> str:
    if "/" not in ip:
        # No CIDR suffix, assume /32
        return f"::ffff:{ip}/128"

    parts = ip.split("/")
    suffix = int(parts[1])
    # Add 96 to the suffix, since ::ffff: is 96 bits
    return f"::ffff:{parts[0]}/{suffix + 96}"
