import os
import pytest
from unittest.mock import patch
from .get_api_url import get_api_url

DEFAULT_API_URL = "https://guard.aikido.dev/"


def test_get_api_url_no_env_var():
    """Test when AIKIDO_ENDPOINT is not set."""
    with patch.dict(os.environ, {}, clear=True):
        assert get_api_url() == DEFAULT_API_URL


def test_get_api_url_valid_url():
    """Test when AIKIDO_ENDPOINT is set to a valid URL."""
    valid_url = "https://example.com/api"
    with patch.dict(os.environ, {"AIKIDO_ENDPOINT": valid_url}):
        assert get_api_url() == valid_url + "/"


def test_get_api_url_invalid_url():
    """Test when AIKIDO_ENDPOINT is set to an invalid URL."""
    invalid_url = "invalid_url"
    with patch.dict(os.environ, {"AIKIDO_ENDPOINT": invalid_url}):
        assert get_api_url() == DEFAULT_API_URL


def test_get_api_url_valid_url_no_trailing_slash():
    """Test when AIKIDO_ENDPOINT is set to a valid URL without a trailing slash."""
    valid_url_no_slash = "https://example.com/api"
    with patch.dict(os.environ, {"AIKIDO_ENDPOINT": valid_url_no_slash}):
        assert get_api_url() == valid_url_no_slash + "/"


def test_get_api_url_no_token_defaults_to_eu():
    """Test when neither AIKIDO_ENDPOINT nor AIKIDO_TOKEN is set."""
    with patch.dict(os.environ, {}, clear=True):
        assert get_api_url() == DEFAULT_API_URL


def test_get_api_url_old_format_token_defaults_to_eu():
    """Test when AIKIDO_TOKEN is set with the old token format."""
    with patch.dict(
        os.environ,
        {"AIKIDO_TOKEN": "AIK_RUNTIME_123_456_random"},
        clear=True,
    ):
        assert get_api_url() == DEFAULT_API_URL


def test_get_api_url_us_region_token():
    """Test when AIKIDO_TOKEN encodes the US region."""
    with patch.dict(
        os.environ,
        {"AIKIDO_TOKEN": "AIK_RUNTIME_123_456_US_random"},
        clear=True,
    ):
        assert get_api_url() == "https://guard.us.aikido.dev/"


def test_get_api_url_me_region_token():
    """Test when AIKIDO_TOKEN encodes the ME region."""
    with patch.dict(
        os.environ,
        {"AIKIDO_TOKEN": "AIK_RUNTIME_123_456_ME_random"},
        clear=True,
    ):
        assert get_api_url() == "https://guard.me.aikido.dev/"


def test_get_api_url_au_region_token():
    """Test when AIKIDO_TOKEN encodes the AU region."""
    with patch.dict(
        os.environ,
        {"AIKIDO_TOKEN": "AIK_RUNTIME_123_456_AU_random"},
        clear=True,
    ):
        assert get_api_url() == "https://guard.au.aikido.dev/"


def test_get_api_url_endpoint_env_var_takes_precedence_over_token():
    """Test that AIKIDO_ENDPOINT overrides region derived from AIKIDO_TOKEN."""
    valid_url = "https://example.com/api"
    with patch.dict(
        os.environ,
        {
            "AIKIDO_ENDPOINT": valid_url,
            "AIKIDO_TOKEN": "AIK_RUNTIME_123_456_US_random",
        },
        clear=True,
    ):
        assert get_api_url() == valid_url + "/"


# You may need to mock the try_parse_url function if it has side effects or is complex
