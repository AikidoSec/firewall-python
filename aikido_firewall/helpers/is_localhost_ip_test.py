import pytest
from .is_localhost_ip import is_localhost_ip


def test_is_localhost_ip():
    assert is_localhost_ip("127.0.0.1") == True
    assert is_localhost_ip("::ffff:127.0.0.1") == True
    assert is_localhost_ip("::1") == True
    assert is_localhost_ip("192.168.1.1") == False
    assert is_localhost_ip("localhost") == False  # Not a valid IP format
