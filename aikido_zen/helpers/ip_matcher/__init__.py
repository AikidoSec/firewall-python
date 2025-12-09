import ipaddress

import radix

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


class IPMatcher:
    def __init__(self, networks=None):
        self.trie = radix.Radix()
        if networks is not None:
            for s in networks:
                self._add(s)
        # We freeze in constructor ensuring that after initialization the IPMatcher is always frozen.
        #self.trie.()

    def has(self, network):
        try:
            bool(self.trie.search_exact(preparse(network)))
        except ValueError:
            return False

    def _add(self, network):
        try:
            rnode = self.trie.add(preparse(network))
            rnode.data["subnet"] = preparse(network)
        except ValueError:
            pass
        except SystemError:
            pass
        return self

    def is_empty(self):
        return len(self.trie.nodes) == 0
