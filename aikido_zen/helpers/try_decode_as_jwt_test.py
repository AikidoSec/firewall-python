import pytest
from aikido_zen.helpers.try_decode_as_jwt import try_decode_as_jwt


def test_returns_false_for_empty_string():
    assert try_decode_as_jwt("") == (False, None)


def test_returns_false_for_invalid_JWT():
    assert try_decode_as_jwt("invalid") == (False, None)
    assert try_decode_as_jwt("invalid.invalid") == (False, None)
    assert try_decode_as_jwt("invalid.invalid.invalid") == (False, None)
    assert try_decode_as_jwt("invalid.invalid.invalid.invalid") == (False, None)


def test_returns_payload_for_invalid_JWT():
    assert try_decode_as_jwt("/;ping%20localhost;.e30=.") == (True, {})
    assert try_decode_as_jwt("/;ping%20localhost;.W10=.") == (True, [])


def test_returns_decoded_JWT_for_valid_JWT():
    assert try_decode_as_jwt(
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwidXNlcm5hbWUiOnsiJG5lIjpudWxsfSwiaWF0IjoxNTE2MjM5MDIyfQ._jhGJw9WzB6gHKPSozTFHDo9NOHs3CNOlvJ8rWy6VrQ"
    ) == (True, {"sub": "1234567890", "username": {"$ne": None}, "iat": 1516239022})


def test_returns_decoded_JWT_for_valid_JWT_with_bearer_prefix():
    assert try_decode_as_jwt(
        "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwidXNlcm5hbWUiOnsiJG5lIjpudWxsfSwiaWF0IjoxNTE2MjM5MDIyfQ._jhGJw9WzB6gHKPSozTFHDo9NOHs3CNOlvJ8rWy6VrQ"
    ) == (True, {"sub": "1234567890", "username": {"$ne": None}, "iat": 1516239022})
