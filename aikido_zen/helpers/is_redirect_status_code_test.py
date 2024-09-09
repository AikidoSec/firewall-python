import pytest
from .is_redirect_status_code import is_redirect_status_code


def test_is_redirect_status_code():
    assert is_redirect_status_code(302) == True
    assert is_redirect_status_code(307) == True

    assert is_redirect_status_code(200) == False
    assert is_redirect_status_code(404) == False
    assert is_redirect_status_code(500) == False
    assert is_redirect_status_code(400) == False
    assert is_redirect_status_code(100) == False
