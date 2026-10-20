import pytest
from unittest.mock import Mock, patch
from . import should_ratelimit


@pytest.mark.parametrize(
    "rate_limited, expected_call",
    [
        (True, True),
        (False, False),
    ],
)
def test_process_should_ratelimit(rate_limited, expected_call):
    """Test rate limiting behavior based on different return values."""
    # Arrange
    connection_manager = Mock()
    data = {
        "route_metadata": {
            "route": "/test",
            "url": "http://example.com/test",
            "method": "GET",
        },
        "remote_address": "192.168.1.1",
        "user": {"id": 1, "name": "Test User"},
        "group": "123",
    }

    with patch(
        "aikido_zen.ratelimiting.should_ratelimit_request",
        return_value=rate_limited,
    ) as mock_should_ratelimit:
        # Act
        should_ratelimit.process(connection_manager, data, None)

    # Assert
    mock_should_ratelimit.assert_called_once_with(
        route_metadata=data["route_metadata"],
        remote_address=data["remote_address"],
        user=data["user"],
        connection_manager=connection_manager,
        group="123",
    )


def test_process_should_ratelimit_no_connection_manager():
    # Arrange
    data = {
        "route_metadata": {
            "route": "/test",
            "url": "http://example.com/test",
            "method": "GET",
        },
        "remote_address": "192.168.1.1",
        "user": {"id": 1, "name": "Test User"},
        "group": None,
    }

    # Act
    result = should_ratelimit.process(None, data, None)  # No connection_manager

    # Assert
    assert result is False  # Ensure the function returns False


def test_process_should_ratelimit_multiple_calls():
    # Arrange
    connection_manager = Mock()
    data = {
        "route_metadata": {
            "route": "/test",
            "url": "http://example.com/test",
            "method": "GET",
        },
        "remote_address": "192.168.1.1",
        "user": {"id": 1, "name": "Test User"},
        "group": None,
    }

    with patch(
        "aikido_zen.ratelimiting.should_ratelimit_request",
        side_effect=[True, False],
    ) as mock_should_ratelimit:
        # Act
        should_ratelimit.process(connection_manager, data, None)  # First call
        should_ratelimit.process(connection_manager, data, None)  # Second call

    # Assert
    mock_should_ratelimit.assert_any_call(
        route_metadata=data["route_metadata"],
        remote_address=data["remote_address"],
        user=data["user"],
        connection_manager=connection_manager,
        group=None,
    )


def test_process_should_ratelimit_with_different_connection_manager():
    """Test with different connection_manager configurations."""
    # Arrange
    connection_manager1 = Mock(name="CloudConnectionManager1")
    connection_manager2 = Mock(name="CloudConnectionManager2")
    data = {
        "route_metadata": {
            "route": "/test",
            "url": "http://example.com/test",
            "method": "GET",
        },
        "remote_address": "192.168.1.1",
        "user": {"id": 1, "name": "Test User"},
        "group": None,
    }

    with patch(
        "aikido_zen.ratelimiting.should_ratelimit_request", return_value=True
    ) as mock_should_ratelimit:
        # Act
        should_ratelimit.process(connection_manager1, data, None)
        should_ratelimit.process(connection_manager2, data, None)

    # Assert
    assert mock_should_ratelimit.call_count == 2
    mock_should_ratelimit.assert_any_call(
        route_metadata=data["route_metadata"],
        remote_address=data["remote_address"],
        user=data["user"],
        connection_manager=connection_manager1,
        group=None,
    )
    mock_should_ratelimit.assert_any_call(
        route_metadata=data["route_metadata"],
        remote_address=data["remote_address"],
        user=data["user"],
        connection_manager=connection_manager2,
        group=None,
    )
