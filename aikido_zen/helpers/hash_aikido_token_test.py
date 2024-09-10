import os
import hashlib
import pytest
from .hash_aikido_token import hash_aikido_token


def test_hash_aikido_token_with_valid_token(monkeypatch):
    """Test the hash_aikido_token function with a valid AIKIDO_TOKEN."""
    # Set the environment variable
    monkeypatch.setenv("AIKIDO_TOKEN", "my_secret_token")

    # Expected hash for "my_secret_token"
    expected_hash = "ddd26ab8c5140fb0dc5bd8cdccd6a0102d09c9bdf2466a5cd718373fd42a17b1"

    # Call the function and assert the result
    assert hash_aikido_token() == expected_hash


def test_hash_aikido_token_with_default(monkeypatch):
    """Test the hash_aikido_token function when AIKIDO_TOKEN is not set."""
    # Ensure the environment variable is not set
    monkeypatch.delenv("AIKIDO_TOKEN", raising=False)

    # Expected hash for the default value
    expected_hash = hashlib.sha256("default".encode("utf-8")).hexdigest()

    # Call the function and assert the result
    assert hash_aikido_token() == expected_hash
