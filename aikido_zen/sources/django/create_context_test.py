import pytest
from unittest.mock import MagicMock
from .create_context import create_context
from ...context import Context

wsgi_request = {
    "REQUEST_METHOD": "GET",
    "HTTP_HEADER_1": "header 1 value",
    "HTTP_HEADER_2": "Header 2 value",
    "RANDOM_VALUE": "Random value",
    "HTTP_COOKIE": "sessionId=abc123xyz456;",
    "wsgi.url_scheme": "http",
    "HTTP_HOST": "localhost:8080",
    "PATH_INFO": "/hello",
    "QUERY_STRING": "user=JohnDoe&age=30&age=35",
    "CONTENT_TYPE": "application/json",
    "REMOTE_ADDR": "198.51.100.23",
}


@pytest.fixture
def mock_request():
    """Fixture to create a mock request object."""
    request = MagicMock()
    request.POST.dict.return_value = {}
    request.content_type = "application/json"
    request.body = '{"key": "value"}'  # Example JSON body
    request.META = wsgi_request
    request.scope = None
    return request


def test_create_context_with_json(mock_request):
    """Test create_context with a JSON request."""
    context: Context = create_context(mock_request)

    # Assertions
    assert {"key": "value"} == context.body


def test_create_context_with_dict(mock_request):
    """Test create_context with a JSON request."""
    mock_request.POST.dict.return_value = {"a": [1, 2], "b": [2, 3]}
    context: Context = create_context(mock_request)

    # Assertions
    assert {"a": [1, 2], "b": [2, 3]} == context.body


def test_create_context_with_dict_error(mock_request):
    """Test create_context with a JSON request."""
    mock_request.POST.dict.side_effect = Exception("too large")
    context: Context = create_context(mock_request)

    # Assertions
    assert {"key": "value"} == context.body


def test_create_context_with_dict_error_and_invalid_json(mock_request):
    """Test create_context with a JSON request."""
    mock_request.POST.dict.side_effect = Exception("too large")
    mock_request.body = '{"key" :: "value"}'  # Invalid json
    context: Context = create_context(mock_request)

    # Assertions
    assert '{"key" :: "value"}' == context.body


def test_create_context_with_complicated_json(mock_request):
    """Test create_context with a JSON request."""
    mock_request.body = '        [{"a": "b"}, 20, 19, false] '
    context: Context = create_context(mock_request)

    # Assertions
    assert [{"a": "b"}, 20, 19, False] == context.body


def test_create_context_with_empty_body(mock_request):
    """Test create_context with an empty body."""
    mock_request.POST.dict.return_value = {}
    mock_request.body = b""  # Simulate an empty body
    context: Context = create_context(mock_request)

    # Assertions
    assert context.body is None


def test_create_context_with_empty_body_string(mock_request):
    """Test create_context with an empty body."""
    mock_request.POST.dict.return_value = {}
    mock_request.body = ""  # Simulate an empty body
    context: Context = create_context(mock_request)

    # Assertions
    assert context.body is None


def test_create_context_with_xml(mock_request):
    """Test create_context with an XML request."""
    mock_request.content_type = "application/xml"
    mock_request.body = "<root><key>value</key></root>"  # Example XML body
    context: Context = create_context(mock_request)
    # Assertions
    assert context.body == "<root><key>value</key></root>"


def test_uses_wsgi(mock_request):
    context: Context = create_context(mock_request)
    # Assertions
    assert "/hello" == context.route
