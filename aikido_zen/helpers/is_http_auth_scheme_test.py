import pytest
from .is_http_auth_scheme import is_http_auth_scheme


def test_is_http_auth_scheme():
    assert is_http_auth_scheme("Bearer") == True
    assert is_http_auth_scheme("BEARER") == True
    assert is_http_auth_scheme("DiGeSt") == True
    assert is_http_auth_scheme("invalid") == False
