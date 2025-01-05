import pytest
from unittest.mock import patch, MagicMock
from aikido_zen.background_process import get_comms
from aikido_zen.helpers.logging import logger
from aikido_zen.thread.thread_cache import get_cache, ThreadCache
from .request_handler import request_handler, post_response


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


@patch("aikido_zen.background_process.get_comms")
def test_post_response_useful_route(mock_get_comms, mock_context):
    """Test post_response when the route is useful."""
    comms = MagicMock()
    mock_get_comms.return_value = comms

    cache = ThreadCache()  # Creates a new cache
    assert cache.routes.routes == {}
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        request_handler("post_response", status_code=200)

    # Check that the route was initialized and updated
    assert cache.routes.routes == {
        "GET:/test/route": {
            "apispec": {},
            "hits": 1,
            "method": "GET",
            "path": "/test/route",
            "hits_delta_since_sync": 1,
        }
    }

    comms.send_data_to_bg_process.assert_called_once_with(
        "INITIALIZE_ROUTE",
        {
            "route": "/test/route",
            "method": "GET",
            "url": "http://localhost:8080/test/route",
        },
    )


@patch("aikido_zen.background_process.get_comms")
def test_post_response_not_useful_route(mock_get_comms, mock_context):
    """Test post_response when the route is not useful."""
    comms = MagicMock()
    mock_get_comms.return_value = comms

    cache = ThreadCache()  # Creates a new cache
    assert cache.routes.routes == {}

    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        request_handler("post_response", status_code=500)

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
        result = request_handler("post_response", status_code=200)

    assert cache.routes.routes == {}
    comms.send_data_to_bg_process.assert_not_called()
