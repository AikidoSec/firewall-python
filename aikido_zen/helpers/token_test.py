import pytest
from aikido_zen.helpers.token import Token, extract_region_from_token


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


# Test extract_region_from_token :
def test_extract_region_from_token_empty():
    assert extract_region_from_token("") == "EU"


def test_extract_region_from_token_none():
    assert extract_region_from_token(None) == "EU"


def test_extract_region_from_token_no_prefix():
    assert extract_region_from_token("my_token") == "EU"


def test_extract_region_from_token_old_format():
    assert extract_region_from_token("AIK_RUNTIME_123_456_random") == "EU"


def test_extract_region_from_token_new_format():
    assert extract_region_from_token("AIK_RUNTIME_123_456_US_random") == "US"


def test_extract_region_from_token_new_format_me():
    assert extract_region_from_token("AIK_RUNTIME_123_456_ME_random") == "ME"


def test_extract_region_from_token_new_format_au():
    assert extract_region_from_token("AIK_RUNTIME_123_456_AU_random") == "AU"
