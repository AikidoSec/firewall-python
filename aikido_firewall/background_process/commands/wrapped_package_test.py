import pytest
from unittest.mock import MagicMock
from .wrapped_package import process_wrapped_package


@pytest.fixture
def mock_reporter():
    """Fixture to create a mock reporter with a packages attribute."""
    reporter = MagicMock()
    reporter.packages = {}
    return reporter


@pytest.fixture
def mock_conn():
    """Fixture to create a mock connection."""
    conn = MagicMock()
    return conn


def test_process_wrapped_package_adds_package(mock_reporter):
    """Test that process_wrapped_package adds a package when reporter is present."""
    data = {"name": "package1", "details": {"version": "1.0.0"}}

    result = process_wrapped_package(mock_reporter, data)

    # Check that the package was added to the reporter's packages
    assert mock_reporter.packages["package1"] == {"version": "1.0.0"}
    assert result is True  # Ensure the function returns True


def test_process_wrapped_package_updates_existing_package(mock_reporter):
    """Test that process_wrapped_package updates an existing package."""
    data = {"name": "package1", "details": {"version": "1.0.0"}}
    mock_reporter.packages["package1"] = {"version": "0.9.0"}  # Existing package

    result = process_wrapped_package(mock_reporter, data)

    # Check that the package was updated
    assert mock_reporter.packages["package1"] == {"version": "1.0.0"}
    assert result is True  # Ensure the function returns True


def test_process_wrapped_package_no_reporter(mock_conn):
    """Test that process_wrapped_package returns False when reporter is not present."""
    data = {"name": "package1", "details": {"version": "1.0.0"}}

    result = process_wrapped_package(None, data)

    # Check that False was returned
    assert result is False


def test_process_wrapped_package_missing_name(mock_reporter):
    """Test that process_wrapped_package handles missing package name."""
    data = {"details": {"version": "1.0.0"}}  # Missing 'name'

    result = process_wrapped_package(mock_reporter, data)

    # Check that the connection sends False (or handle it gracefully)
    assert result is False  # Ensure the function returns False


def test_process_wrapped_package_missing_details(mock_reporter):
    """Test that process_wrapped_package handles missing package details."""
    data = {"name": "package1"}  # Missing 'details'

    result = process_wrapped_package(mock_reporter, data)

    # Check that the function returns False
    assert result is False


def test_process_wrapped_package_empty_details(mock_reporter):
    """Test that process_wrapped_package adds a package with empty details."""
    data = {"name": "package1", "details": {}}

    result = process_wrapped_package(mock_reporter, data)

    # Check that the package was added with empty details
    assert mock_reporter.packages["package1"] == {}
    assert result is True  # Ensure the function returns True


def test_process_wrapped_package_multiple_calls(mock_reporter):
    """Test that multiple calls to process_wrapped_package work correctly."""
    data1 = {"name": "package1", "details": {"version": "1.0.0"}}
    data2 = {"name": "package2", "details": {"version": "2.0.0"}}

    result1 = process_wrapped_package(mock_reporter, data1)
    result2 = process_wrapped_package(mock_reporter, data2)

    # Check that both packages were added
    assert mock_reporter.packages["package1"] == {"version": "1.0.0"}
    assert mock_reporter.packages["package2"] == {"version": "2.0.0"}
    assert result1 is True  # Ensure the first call returns True
    assert result2 is True  # Ensure the second call returns True
