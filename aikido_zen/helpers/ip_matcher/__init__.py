import weakref

from aikido_zen.helpers import zen_internals


class IPMatcher:
    def __init__(self, networks=None):
        # json.loads can return lone surrogates such as "\udc80", and .encode() raises on
        # them, which would fail the whole list update. Valid networks are ASCII.
        self._networks = [
            network
            for network in networks or []
            if isinstance(network, str) and network.isascii()
        ]
        self._handle = zen_internals.ip_matcher_create(
            [network.encode() for network in self._networks]
        )
        if self._handle is not None:
            weakref.finalize(self, zen_internals.ip_matcher_free, self._handle)

    def is_built(self):
        return self._handle is not None

    def has(self, network):
        if self._handle is None:
            return False
        if not isinstance(network, str) or not network.isascii():
            return False
        return zen_internals.ip_matcher_has(self._handle, network.encode())

    def is_empty(self):
        return len(self._networks) == 0

    def __reduce__(self):
        return self.__class__, (self._networks,)
