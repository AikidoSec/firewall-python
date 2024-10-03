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


# You may need to mock the try_parse_url function if it has side effects or is complex
