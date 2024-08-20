import pytest
from unittest.mock import Mock, patch

from .should_ratelimit import process_should_ratelimit


@pytest.fixture
def mock_bg_process():
    """Fixture to create a mock bg_process."""
    return Mock()


@pytest.fixture
def mock_conn():
    """Fixture to create a mock connection."""
    return Mock()


@pytest.mark.parametrize(
    "should_ratelimit, expected_call",
    [
        (True, True),
        (False, False),
    ],
)
def test_process_should_ratelimit(
    mock_bg_process, mock_conn, should_ratelimit, expected_call
):
    """Test rate limiting behavior based on different return values."""
    # Arrange
    mock_bg_process.reporter = Mock()
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
    ):
        # Act
        process_should_ratelimit(mock_bg_process, data, mock_conn)

    # Assert
    mock_conn.send.assert_called_once_with(expected_call)


def test_process_should_ratelimit_multiple_calls(mock_bg_process, mock_conn):
    """Test multiple calls to process_should_ratelimit."""
    # Arrange
    mock_bg_process.reporter = Mock()
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
    ):
        # Act
        process_should_ratelimit(mock_bg_process, data, mock_conn)  # First call
        process_should_ratelimit(mock_bg_process, data, mock_conn)  # Second call

    # Assert
    assert mock_conn.send.call_count == 2
    mock_conn.send.assert_any_call(True)
    mock_conn.send.assert_any_call(False)


def test_process_should_ratelimit_with_different_reporter(mock_conn):
    """Test with different reporter configurations."""
    # Arrange
    mock_bg_process_1 = Mock()
    mock_bg_process_1.reporter = Mock(name="Reporter1")
    mock_bg_process_2 = Mock()
    mock_bg_process_2.reporter = Mock(name="Reporter2")
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
    ):
        # Act
        process_should_ratelimit(mock_bg_process_1, data, mock_conn)
        process_should_ratelimit(mock_bg_process_2, data, mock_conn)

    # Assert
    assert mock_conn.send.call_count == 2
    mock_conn.send.assert_any_call(True)
    mock_conn.send.assert_any_call(True)
