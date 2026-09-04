import ipaddress

from aikido_zen.helpers.ip_matcher.native import create_ip_matcher
from aikido_zen.helpers.ip_matcher_fallback import IPMatcher as FallbackIPMatcher


def preparse(network: str):
    candidate = network.strip()
    if candidate.startswith("["):
        closing_bracket = candidate.rfind("]")
        if closing_bracket < 0:
            return network
        candidate = candidate[1:closing_bracket]
    if ":" not in candidate or "%" in candidate or "ffff" not in candidate.lower():
        return network

    try:
        mapped = ipaddress.IPv6Address(candidate).ipv4_mapped
    except ValueError:
        return network
    return str(mapped) if mapped else network


def _collect_networks(networks):
    if networks is None:
        return ()

    collected = []
    try:
        for network in networks:
            if isinstance(network, str):
                collected.append(network)
    except Exception:
        pass
    return tuple(collected)


def _create_fallback(networks):
    try:
        return FallbackIPMatcher(networks)
    except Exception:
        return FallbackIPMatcher()


class IPMatcher:
    def __init__(self, networks=None):
        self._networks = _collect_networks(networks)
        self._native = create_ip_matcher(self._networks)
        self._fallback = (
            _create_fallback(self._networks) if self._native is None else None
        )

    def has(self, network):
        if not isinstance(network, str):
            return False

        try:
            if self._has(network):
                return True
            mapped_ipv4 = preparse(network)
            return mapped_ipv4 != network and self._has(mapped_ipv4)
        except Exception:
            return False

    def _has(self, network):
        matcher = self._native or self._fallback
        return matcher is not None and matcher.has(network)

    def is_empty(self):
        if self._fallback is None:
            self._fallback = _create_fallback(self._networks)
        return self._fallback.is_empty()

    def __reduce__(self):
        return self.__class__, (self._networks,)
