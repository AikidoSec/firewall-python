import ipaddress

try:
    import pytricia

    PYTRICIA_AVAILABLE = True
except ImportError:
    PYTRICIA_AVAILABLE = False
    from aikido_zen.helpers.logging import logger

    logger.warning(
        "pytricia is not available. This happens on windows devices where pytricia is not supported yet."
        "Using fallback, this may result in slower performance."
        "You can try to install pytricia for better performance: pip install pytricia"
    )


def preparse(network: str) -> str:
    # Remove the brackets around IPv6 addresses if they are there.
    network = network.strip("[]")
    try:
        ip = ipaddress.IPv6Address(network)
        if ip.ipv4_mapped:
            return str(ip.ipv4_mapped)
    except ValueError:
        pass
    return network


if PYTRICIA_AVAILABLE:

    class IPMatcher:
        def __init__(self, networks=None):
            self.trie = pytricia.PyTricia(128)
            if networks is not None:
                for s in networks:
                    self._add(s)
            # We freeze in constructor ensuring that after initialization the IPMatcher is always frozen.
            self.trie.freeze()

        def has(self, network):
            try:
                return self.trie.get(preparse(network)) is not None
            except ValueError:
                return False

        def _add(self, network):
            try:
                self.trie[preparse(network)] = True
            except ValueError:
                pass
            except SystemError:
                # SystemError's have been known to occur in the PyTricia library (see issue #34 e.g.),
                # best to play it safe and catch these errors.
                pass
            return self

        def is_empty(self):
            return len(self.trie) == 0

else:
    # Fallback to pure Python implementation - this happens on windows machines since pytricia is not
    # fully supported there.
    from aikido_zen.helpers.ip_matcher_fallback import IPMatcher  # noqa: F401
