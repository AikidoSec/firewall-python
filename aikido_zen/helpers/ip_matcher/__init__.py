import pytricia


class IPMatcher:
    def __init__(self, networks=None):
        self.trie = pytricia.PyTricia(128)
        if networks is not None:
            for s in networks:
                self._add(s)
        # We freeze in constructor ensuring that after initialization the IPMatcher is always frozen.
        self.trie.freeze()

    def has(self, network):
        """
        Checks if the given IP address or network is in the list of networks.
        """
        try:
            return self.trie.get(network) is not None
        except ValueError:
            return False

    def _add(self, network):
        """
        Adds a network to the trie.
        """
        try:
            self.trie[network] = True
        except ValueError:
            pass
        except SystemError:
            pass
        return self

    def is_empty(self):
        return len(self.trie) == 0

    def freeze(self):
        self.trie.freeze()
        return self
