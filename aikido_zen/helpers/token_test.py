import pytest
from aikido_zen.helpers.token import Token


# Test Token Class :
def test_token_valid_string():
    token_str = "my_token"
    token = Token(token_str)
    assert str(token) == token_str


def test_token_empty_string():
    with pytest.raises(ValueError):
        Token("")


def test_token_invalid_type():
    with pytest.raises(ValueError):
        Token(123)


def test_token_instance():
    token_str = "my_token"
    token = Token(token_str)
    assert isinstance(token, Token)
