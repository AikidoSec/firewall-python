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


def test_process_wrapped_package_adds_package(mock_reporter, mock_conn):
    """Test that process_wrapped_package adds a package when reporter is present."""
    data = {"name": "package1", "details": {"version": "1.0.0"}}

    process_wrapped_package(mock_reporter, data, mock_conn)

    # Check that the package was added to the reporter's packages
    assert mock_reporter.packages["package1"] == {"version": "1.0.0"}
    mock_conn.send.assert_called_once_with(True)


def test_process_wrapped_package_updates_existing_package(mock_reporter, mock_conn):
    """Test that process_wrapped_package updates an existing package."""
    data = {"name": "package1", "details": {"version": "1.0.0"}}
    mock_reporter.packages["package1"] = {"version": "0.9.0"}  # Existing package

    process_wrapped_package(mock_reporter, data, mock_conn)

    # Check that the package was updated
    assert mock_reporter.packages["package1"] == {"version": "1.0.0"}
    mock_conn.send.assert_called_once_with(True)


def test_process_wrapped_package_no_reporter(mock_conn):
    """Test that process_wrapped_package sends False when reporter is not present."""
    data = {"name": "package1", "details": {"version": "1.0.0"}}

    process_wrapped_package(None, data, mock_conn)

    # Check that False was sent through the connection
    mock_conn.send.assert_called_once_with(False)


def test_process_wrapped_package_missing_name(mock_reporter, mock_conn):
    """Test that process_wrapped_package handles missing package name."""
    data = {"details": {"version": "1.0.0"}}  # Missing 'name'

    process_wrapped_package(mock_reporter, data, mock_conn)

    # Check that the connection sends False (or handle it gracefully)
    mock_conn.send.assert_called_once_with(False)  # Assuming it still sends True


def test_process_wrapped_package_missing_details(mock_reporter, mock_conn):
    """Test that process_wrapped_package handles missing package details."""
    data = {"name": "package1"}  # Missing 'details'

    process_wrapped_package(mock_reporter, data, mock_conn)
    mock_conn.send.assert_called_once_with(False)


def test_process_wrapped_package_empty_details(mock_reporter, mock_conn):
    """Test that process_wrapped_package adds a package with empty details."""
    data = {"name": "package1", "details": {}}

    process_wrapped_package(mock_reporter, data, mock_conn)

    # Check that the package was added with empty details
    assert mock_reporter.packages["package1"] == {}
    mock_conn.send.assert_called_once_with(True)


def test_process_wrapped_package_multiple_calls(mock_reporter, mock_conn):
    """Test that multiple calls to process_wrapped_package work correctly."""
    data1 = {"name": "package1", "details": {"version": "1.0.0"}}
    data2 = {"name": "package2", "details": {"version": "2.0.0"}}

    process_wrapped_package(mock_reporter, data1, mock_conn)
    process_wrapped_package(mock_reporter, data2, mock_conn)

    # Check that both packages were added
    assert mock_reporter.packages["package1"] == {"version": "1.0.0"}
    assert mock_reporter.packages["package2"] == {"version": "2.0.0"}
    assert mock_conn.send.call_count == 2  # Ensure send was called twice
