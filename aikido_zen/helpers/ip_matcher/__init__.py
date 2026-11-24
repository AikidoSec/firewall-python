import weakref

from aikido_zen.helpers import zen_internals


class IPMatcher:
    def __init__(self, networks=None):
        # json.loads can return lone surrogates such as "\udc80", and .encode() raises on
        # them, which would fail the whole list update. Valid networks are ASCII.
        # The library splits on newlines, so a newline would turn one entry into two,
        # and an empty string sent alone would not count as a rejected entry.
        networks = list(networks or [])
        self._networks = [
            network
            for network in networks
            if isinstance(network, str)
            and network
            and network.isascii()
            and "\n" not in network
        ]
        self._skipped_count = len(networks) - len(self._networks)
        self._handle = zen_internals.ip_matcher_create(
            "\n".join(self._networks).encode()
        )
        if self._handle is not None:
            finalizer = weakref.finalize(
                self, zen_internals.ip_matcher_free, self._handle
            )
            # Exit handlers that run later can still check IPs, so don't free at exit.
            finalizer.atexit = False

    def is_built(self):
        return self._handle is not None

    def rejected_count(self):
        if self._handle is None:
            return self._skipped_count
        return self._skipped_count + zen_internals.ip_matcher_rejected_count(
            self._handle
        )

    def has(self, network):
        if self._handle is None:
            return False
        if not isinstance(network, str) or not network.isascii():
            return False
        return zen_internals.ip_matcher_has(self._handle, network.encode())

    def is_empty(self):
        # Networks the library rejected match nothing, so they do not count.
        return self.rejected_count() == len(self._networks) + self._skipped_count

    def __reduce__(self):
        return self.__class__, (self._networks,)
