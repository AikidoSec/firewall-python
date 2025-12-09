import pytricia


class IPMatcher:
    def __init__(self, networks=None):
        self.trie = pytricia.PyTricia(128)
        if networks is not None:
            for s in networks:
                self.add(s)

    def has(self, network):
        """
        Checks if the given IP address or network is in the list of networks.
        """
        try:
            return self.trie.get(network) is not None
        except ValueError:
            return False

    def add(self, network):
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
