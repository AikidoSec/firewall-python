import pytest
from unittest.mock import MagicMock, patch
from .route import process_route


@pytest.fixture
def mock_reporter():
    """Fixture to create a mock reporter with a routes attribute."""
    reporter = MagicMock()
    reporter.routes = MagicMock()
    return reporter


def test_process_route_adds_route(mock_reporter):
    """Test that process_route adds a route when reporter is present."""
    data = ["GET", "/api/test"]

    process_route(mock_reporter, data, None)  # conn is not used in this function

    # Check that the add_route method was called with the correct arguments
    mock_reporter.routes.add_route.assert_called_once_with(
        method="GET", path="/api/test"
    )


def test_process_route_no_reporter():
    """Test that process_route does nothing when reporter is not present."""
    data = ["POST", "/api/test"]

    process_route(None, data, None)  # conn is not used in this function

    # Check that no error occurs
