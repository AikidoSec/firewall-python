import ipaddress
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional, Union

from aikido_zen.helpers.ip_matcher import IPMatcher
from aikido_zen.helpers.logging import logger


@dataclass(frozen=True)
class BooleanTrustProxy:
    value: bool


@dataclass(frozen=True)
class CountTrustProxy:
    value: int


@dataclass(frozen=True)
class CIDRTrustProxy:
    matcher: IPMatcher


TrustProxyConfig = Union[BooleanTrustProxy, CountTrustProxy, CIDRTrustProxy]


def get_trust_proxy_config() -> TrustProxyConfig:
    return parse_trust_proxy(os.getenv("AIKIDO_TRUST_PROXY"))


@lru_cache(maxsize=1)
def parse_trust_proxy(value: Optional[str]) -> TrustProxyConfig:
    value = (value or "").strip()
    if not value:
        return BooleanTrustProxy(True)
    if re.fullmatch(r"[0-9]+", value):
        try:
            count = int(value)
        except ValueError:
            return BooleanTrustProxy(False)
        if count > 0:
            return CountTrustProxy(count)
    if value.lower() in ("true", "1", "yes", "y", "on"):
        return BooleanTrustProxy(True)
    if "." in value or ":" in value:
        entries = [entry for entry in map(str.strip, value.split(",")) if entry]
        ranges = [r for r in map(_proxy_range, entries) if r]
        if len(ranges) < len(entries):
            logger.warning("Ignoring invalid trusted proxy ranges.")
        return CIDRTrustProxy(IPMatcher(ranges))
    if value.lower() not in ("false", "0", "no", "n", "off"):
        logger.warning("Ignoring an invalid trusted proxy setting.")
    return BooleanTrustProxy(False)


def _proxy_range(entry: str) -> Optional[str]:
    try:
        network = ipaddress.ip_network(entry.strip("[]"), strict=False)
    except ValueError:
        return None
    # Stored as IPv4 so the proxy also matches when it connects over IPv4.
    mapped = getattr(network.network_address, "ipv4_mapped", None)
    if mapped is not None and network.prefixlen >= 96:
        return f"{mapped}/{network.prefixlen - 96}"
    return str(network)


def is_trusted_proxy_request(remote_address: Optional[str]) -> bool:
    config = get_trust_proxy_config()
    if isinstance(config, BooleanTrustProxy):
        return config.value
    if isinstance(config, CIDRTrustProxy):
        return bool(remote_address) and config.matcher.has(remote_address)
    return True
