import pytest
from .inspect_getaddrinfo_result import (
    inspect_getaddrinfo_result,
    get_metadata_for_ssrf_attack,
)


def test_get_metadata_for_ssrf_attack():
    assert get_metadata_for_ssrf_attack("hostname2", None) == {"hostname": "hostname2"}
    assert get_metadata_for_ssrf_attack("hostname3", 443) == {
        "hostname": "hostname3",
        "port": "443",
    }
