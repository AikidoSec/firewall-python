import pytest
from .feature_flags import is_feature_enabled
import os

ENV_PREFIX = "AIKIDO_FEATURE_"


def test_feature_enabled_true(monkeypatch):
    """Test when the feature is enabled."""
    monkeypatch.setenv(ENV_PREFIX + "TEST_FEATURE", "true")
    assert is_feature_enabled("test_feature") is True


def test_feature_enabled_true_with_one(monkeypatch):
    """Test when the feature is enabled with '1'."""
    monkeypatch.setenv(ENV_PREFIX + "TEST_FEATURE", "1")
    assert is_feature_enabled("test_feature") is True


def test_feature_enabled_true_uppercase(monkeypatch):
    """Test when the feature is enabled with 'TRUE'."""
    monkeypatch.setenv(ENV_PREFIX + "TEST_FEATURE", "TRUE")
    assert is_feature_enabled("test_feature") is True


def test_feature_enabled_true_mixed_case(monkeypatch):
    """Test when the feature is enabled with 'TrUe'."""
    monkeypatch.setenv(ENV_PREFIX + "TEST_FEATURE", "TrUe")
    assert is_feature_enabled("test_feature") is True


def test_feature_enabled_false(monkeypatch):
    """Test when the feature is disabled."""
    monkeypatch.setenv(ENV_PREFIX + "TEST_FEATURE", "false")
    assert is_feature_enabled("test_feature") is False


def test_feature_enabled_false_with_zero(monkeypatch):
    """Test when the feature is disabled with '0'."""
    monkeypatch.setenv(ENV_PREFIX + "TEST_FEATURE", "0")
    assert is_feature_enabled("test_feature") is False


def test_feature_enabled_false_uppercase(monkeypatch):
    """Test when the feature is disabled with 'FALSE'."""
    monkeypatch.setenv(ENV_PREFIX + "TEST_FEATURE", "FALSE")
    assert is_feature_enabled("test_feature") is False


def test_feature_enabled_false_mixed_case(monkeypatch):
    """Test when the feature is disabled with 'FaLsE'."""
    monkeypatch.setenv(ENV_PREFIX + "TEST_FEATURE", "FaLsE")
    assert is_feature_enabled("test_feature") is False


def test_feature_enabled_not_set(monkeypatch):
    """Test when the feature is not set in the environment."""
    monkeypatch.delenv(
        ENV_PREFIX + "TEST_FEATURE", raising=False
    )  # Ensure the variable is not set
    assert is_feature_enabled("test_feature") is False


def test_feature_enabled_invalid_value(monkeypatch):
    """Test when the feature is set to an invalid value."""
    monkeypatch.setenv(ENV_PREFIX + "TEST_FEATURE", "invalid_value")
    assert is_feature_enabled("test_feature") is False


def test_feature_enabled_with_underscore(monkeypatch):
    """Test when the feature is enabled with underscores in the name."""
    monkeypatch.setenv(ENV_PREFIX + "TEST_FEATURE", "true")
    assert is_feature_enabled("test_Feature") is True


def test_feature_enabled_with_underscore_uppercase(monkeypatch):
    """Test when the feature is enabled with underscores and uppercase."""
    monkeypatch.setenv(ENV_PREFIX + "TEST_FEATURE", "TRUE")
    assert is_feature_enabled("test_Feature") is True


def test_feature_enabled_with_underscore_mixed_case(monkeypatch):
    """Test when the feature is enabled with underscores and mixed case."""
    monkeypatch.setenv(ENV_PREFIX + "TEST_FEATURE", "TrUe")
    assert is_feature_enabled("test_Feature") is True
