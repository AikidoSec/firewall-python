import pytest
from .map_ipv4_to_ipv6 import map_ipv4_to_ipv6


@pytest.mark.parametrize(
    "ip, expected",
    [
        ("127.0.0.0", "::ffff:127.0.0.0/128"),
        ("127.0.0.0/8", "::ffff:127.0.0.0/104"),
        ("10.0.0.0", "::ffff:10.0.0.0/128"),
        ("10.0.0.0/8", "::ffff:10.0.0.0/104"),
        ("10.0.0.1", "::ffff:10.0.0.1/128"),
        ("10.0.0.1/8", "::ffff:10.0.0.1/104"),
        ("192.168.0.0/16", "::ffff:192.168.0.0/112"),
        ("172.16.0.0/12", "::ffff:172.16.0.0/108"),
    ],
)
def test_map_ipv4_to_ipv6(ip, expected):
    assert map_ipv4_to_ipv6(ip) == expected
