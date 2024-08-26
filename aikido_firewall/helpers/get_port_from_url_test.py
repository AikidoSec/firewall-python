import pytest
from .get_port_from_url import get_port_from_url


def test_get_port_from_url():
    assert get_port_from_url("http://localhost:4000") == 4000
    assert get_port_from_url("http://localhost") == 80
    assert get_port_from_url("https://test.com:8080/test?abc=123") == 8080
    assert get_port_from_url("https://localhost") == 443
    assert get_port_from_url("ftp://localhost") is None
