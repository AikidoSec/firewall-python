import ipaddress

try:
    from ipset_c import IPSet

    IPSET_C_AVAILABLE = True
except ImportError:
    IPSET_C_AVAILABLE = False
    from aikido_zen.helpers.logging import logger

    logger.warning(
        "ipset_c is not available on this platform/architecture."
        "Using fallback, this may result in slower performance."
        "You can try to install ipset_c for better performance: pip install ipset_c"
    )


IPV4_MAPPED_IPV6_BASE = ipaddress.ip_network("::ffff:0:0/96")


def preparse(network: str):
    """
    Strips the brackets around IPv6 addresses if they are there and parses the
    network into an ipaddress network object. IPv4-mapped IPv6 networks (e.g.
    ::ffff:127.0.0.1) are converted to their plain IPv4 equivalent.
    Returns None if the network is invalid.
    """
    network = network.strip("[]")
    try:
        net = ipaddress.ip_network(network, strict=False)
    except ValueError:
        return None
    if net.version == 6 and net.subnet_of(IPV4_MAPPED_IPV6_BASE):
        ipv4_addr = net.network_address.ipv4_mapped
        return ipaddress.ip_network(f"{ipv4_addr}/{net.prefixlen - 96}", strict=False)
    return net


if IPSET_C_AVAILABLE:

    class IPMatcher:
        def __init__(self, networks=None):
            v4_cidrs = []
            v6_cidrs = []
            if networks is not None:
                for s in networks:
                    net = preparse(s)
                    if net is None:
                        continue
                    (v4_cidrs if net.version == 4 else v6_cidrs).append(str(net))
            self.v4 = IPSet(v4_cidrs)
            self.v6 = IPSet(v6_cidrs)

        def has(self, network):
            net = preparse(network)
            if net is None:
                return False
            ipset = self.v4 if net.version == 4 else self.v6
            return ipset.isContainsCidr(str(net))

        def is_empty(self):
            return self.v4.size == 0 and self.v6.size == 0

else:
    # Fallback to pure Python implementation - this happens when ipset_c is not
    # available for the current platform/architecture.
    from aikido_zen.helpers.ip_matcher_fallback import IPMatcher  # noqa: F401
