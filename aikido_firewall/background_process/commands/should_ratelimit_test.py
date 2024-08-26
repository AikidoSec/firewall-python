import pytest
from unittest.mock import Mock, patch
from .should_ratelimit import process_should_ratelimit


@pytest.mark.parametrize(
    "should_ratelimit, expected_call",
    [
        (True, True),
        (False, False),
    ],
)
def test_process_should_ratelimit(should_ratelimit, expected_call):
    """Test rate limiting behavior based on different return values."""
    # Arrange
    reporter = Mock()
    data = {
        "route_metadata": {
            "route": "/test",
            "url": "http://example.com/test",
            "method": "GET",
        },
        "remote_address": "192.168.1.1",
        "user": {"id": 1, "name": "Test User"},
    }

    with patch(
        "aikido_firewall.ratelimiting.should_ratelimit_request",
        return_value=should_ratelimit,
    ) as mock_should_ratelimit:
        # Act
        result = process_should_ratelimit(reporter, data)
        assert result == expected_call

    # Assert
    mock_should_ratelimit.assert_called_once_with(
        route_metadata=data["route_metadata"],
        remote_address=data["remote_address"],
        user=data["user"],
        reporter=reporter,
    )


def test_process_should_ratelimit_no_reporter():
    """Test that process_should_ratelimit does nothing when reporter is not present."""
    # Arrange
    data = {
        "route_metadata": {
            "route": "/test",
            "url": "http://example.com/test",
            "method": "GET",
        },
        "remote_address": "192.168.1.1",
        "user": {"id": 1, "name": "Test User"},
    }

    # Act
    result = process_should_ratelimit(None, data)  # No reporter

    # Assert
    assert result is False  # Ensure the function returns False


def test_process_should_ratelimit_multiple_calls():
    """Test multiple calls to process_should_ratelimit."""
    # Arrange
    reporter = Mock()
    data = {
        "route_metadata": {
            "route": "/test",
            "url": "http://example.com/test",
            "method": "GET",
        },
        "remote_address": "192.168.1.1",
        "user": {"id": 1, "name": "Test User"},
    }

    with patch(
        "aikido_firewall.ratelimiting.should_ratelimit_request",
        side_effect=[True, False],
    ) as mock_should_ratelimit:
        # Act
        process_should_ratelimit(reporter, data)  # First call
        process_should_ratelimit(reporter, data)  # Second call

    # Assert
    mock_should_ratelimit.assert_any_call(
        route_metadata=data["route_metadata"],
        remote_address=data["remote_address"],
        user=data["user"],
        reporter=reporter,
    )


def test_process_should_ratelimit_with_different_reporter():
    """Test with different reporter configurations."""
    # Arrange
    reporter1 = Mock(name="Reporter1")
    reporter2 = Mock(name="Reporter2")
    data = {
        "route_metadata": {
            "route": "/test",
            "url": "http://example.com/test",
            "method": "GET",
        },
        "remote_address": "192.168.1.1",
        "user": {"id": 1, "name": "Test User"},
    }

    with patch(
        "aikido_firewall.ratelimiting.should_ratelimit_request", return_value=True
    ) as mock_should_ratelimit:
        # Act
        process_should_ratelimit(reporter1, data)
        process_should_ratelimit(reporter2, data)

    # Assert
    assert mock_should_ratelimit.call_count == 2
    mock_should_ratelimit.assert_any_call(
        route_metadata=data["route_metadata"],
        remote_address=data["remote_address"],
        user=data["user"],
        reporter=reporter1,
    )
    mock_should_ratelimit.assert_any_call(
        route_metadata=data["route_metadata"],
        remote_address=data["remote_address"],
        user=data["user"],
        reporter=reporter2,
    )
