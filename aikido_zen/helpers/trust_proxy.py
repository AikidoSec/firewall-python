import os
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional, Union

from aikido_zen.helpers.ip_matcher import IPMatcher, preparse


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
    if not value:
        return BooleanTrustProxy(True)
    if re.fullmatch(r"[0-9]+", value):
        count = int(value)
        if count > 0:
            return CountTrustProxy(count)
    if value.lower() in ("true", "1", "yes", "y", "on"):
        return BooleanTrustProxy(True)
    if "." in value or ":" in value:
        ranges = [entry.strip() for entry in value.split(",") if entry.strip()]
        return CIDRTrustProxy(IPMatcher(ranges))
    return BooleanTrustProxy(False)


def is_trusted_proxy_request(remote_address: Optional[str]) -> bool:
    config = get_trust_proxy_config()
    if isinstance(config, BooleanTrustProxy):
        return config.value
    if isinstance(config, CIDRTrustProxy):
        return bool(remote_address) and config.matcher.has(preparse(remote_address))
    return True
