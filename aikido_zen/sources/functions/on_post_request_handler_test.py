from unittest.mock import patch, MagicMock
import pytest

from aikido_zen.sources.functions.on_post_request_handler import on_post_request_handler
from aikido_zen.thread.thread_cache import ThreadCache, get_cache


@pytest.fixture
def mock_context():
    """Fixture to create a mock context."""
    context = MagicMock()
    context.route = "/test/route"
    context.method = "GET"
    context.get_route_metadata.return_value = {
        "route": "/test/route",
        "method": "GET",
        "url": "http://localhost:8080/test/route",
    }
    return context


@pytest.fixture(autouse=True)
def run_around_tests():
    get_cache().reset()
    yield
    get_cache().reset()


@patch("aikido_zen.background_process.get_comms")
def test_post_response_useful_route(mock_get_comms, mock_context):
    """Test post_response when the route is useful."""
    comms = MagicMock()
    mock_get_comms.return_value = comms

    assert get_cache().routes.routes == {}
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        on_post_request_handler(status_code=200)

    # Check that the route was initialized and updated
    assert get_cache().routes.routes == {
        "GET:/test/route": {
            "apispec": {},
            "hits": 1,
            "method": "GET",
            "path": "/test/route",
            "hits_delta_since_sync": 1,
        }
    }


@patch("aikido_zen.background_process.get_comms")
def test_post_response_not_useful_route(mock_get_comms, mock_context):
    """Test post_response when the route is not useful."""
    comms = MagicMock()
    mock_get_comms.return_value = comms

    cache = ThreadCache()  # Creates a new cache
    assert cache.routes.routes == {}

    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        on_post_request_handler(status_code=500)

    assert cache.routes.routes == {}
    comms.send_data_to_bg_process.assert_not_called()


@patch("aikido_zen.background_process.get_comms")
def test_post_response_no_context(mock_get_comms):
    """Test post_response when there is no context."""
    comms = MagicMock()
    mock_get_comms.return_value = comms

    cache = ThreadCache()  # Creates a new cache
    assert cache.routes.routes == {}

    # Simulate no context
    with patch("aikido_zen.context.get_current_context", return_value=None):
        on_post_request_handler(status_code=200)

    assert cache.routes.routes == {}
    comms.send_data_to_bg_process.assert_not_called()
