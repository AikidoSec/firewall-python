import pytest
from .get_port_from_url import get_port_from_url
from urllib.parse import urlparse


def test_get_port_from_url():
    assert get_port_from_url("http://localhost:4000") == 4000
    assert get_port_from_url("http://localhost") == 80
    assert get_port_from_url("https://test.com:8080/test?abc=123") == 8080
    assert get_port_from_url("https://localhost") == 443
    assert get_port_from_url("ftp://localhost") is None
    assert get_port_from_url("http://localhost:1337\\u0000asd.php") is None
    assert get_port_from_url("http://localhost:123123/asd.php") is None


def test_get_port_from_parsed_url():
    assert get_port_from_url(urlparse("http://localhost:4000"), True) == 4000
    assert get_port_from_url(urlparse("http://localhost"), True) == 80
    assert (
        get_port_from_url(urlparse("https://test.com:8080/test?abc=123"), True) == 8080
    )
    assert get_port_from_url(urlparse("https://localhost"), True) == 443
    assert get_port_from_url(urlparse("ftp://localhost"), True) is None
    assert (
        get_port_from_url(urlparse("http://localhost:1337\\u0000asd.php"), True) is None
    )
    assert get_port_from_url(urlparse("http://localhost:123123/asd.php"), True) is None
