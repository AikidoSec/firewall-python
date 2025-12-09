import pytricia


def preparse(network: str) -> str:
    # Remove the brackets around IPv6 addresses if they are there.
    network = network.strip("[]")
    return network


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
            pass
        return self

    def is_empty(self):
        return len(self.trie) == 0
