import pytest
from unittest.mock import MagicMock
from .run_init_stage import run_init_stage
from ...context import Context, get_current_context, current_context
from ...helpers.add_ip_address_to_blocklist import add_ip_address_to_blocklist
from ...helpers.blocklist import BlockList
from ...thread.thread_cache import ThreadCache
from ...thread.thread_cache_test import thread_cache

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
asgi_scope = {
    "method": "PUT",
    "headers": [(b"COOKIE", b"a=b; c=d"), (b"header1_test-2", b"testValue2198&")],
    "query_string": b"a=b&b=d",
    "client": ["1.1.1.1"],
    "server": ["192.168.0.1", 443],
    "scheme": "https",
    "root_path": "192.168.0.1",
    "path": "192.168.0.1/a/b/c/d",
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


@pytest.fixture(autouse=True)
def run_around_tests():
    yield
    # Make sure to reset context after every test so it does not
    # interfere with other tests
    current_context.set(None)
    ThreadCache()  # Reset thread cache


def test_run_init_stage_with_json(mock_request):
    """Test run_init_stage with a JSON request."""
    run_init_stage(mock_request)

    # Assertions
    context: Context = get_current_context()
    assert {"key": "value"} == context.body


def test_run_init_stage_with_dict(mock_request):
    """Test run_init_stage with a JSON request."""
    mock_request.POST.dict.return_value = {"a": [1, 2], "b": [2, 3]}
    run_init_stage(mock_request)

    # Assertions
    context: Context = get_current_context()
    assert {"a": [1, 2], "b": [2, 3]} == context.body


class MyThreadCache(ThreadCache):
    def renew_if_ttl_expired(self):
        return


def test_run_init_stage_not_bypassed(mock_request):
    """Test run_init_stage with a JSON request."""
    mock_request.POST.dict.return_value = {"a": [1, 2], "b": [2, 3]}
    thread_cache = MyThreadCache()
    thread_cache.config.bypassed_ips = BlockList()
    add_ip_address_to_blocklist("1.2.3.4", thread_cache.config.bypassed_ips)
    add_ip_address_to_blocklist("5.6.7.8", thread_cache.config.bypassed_ips)
    assert thread_cache.reqs == 0
    run_init_stage(mock_request)

    # Assertions
    context: Context = get_current_context()
    assert {"a": [1, 2], "b": [2, 3]} == context.body
    assert thread_cache.reqs == 1

    # Bypassed
    thread_cache.config.bypassed_ips = BlockList()
    add_ip_address_to_blocklist("1.2.3.4", thread_cache.config.bypassed_ips)
    add_ip_address_to_blocklist("5.6.7.8", thread_cache.config.bypassed_ips)
    add_ip_address_to_blocklist("198.51.100.23", thread_cache.config.bypassed_ips)
    run_init_stage(mock_request)
    assert get_current_context() is None
    assert thread_cache.reqs == 2


def test_run_init_stage_with_dict_error(mock_request):
    """Test run_init_stage with a JSON request."""
    mock_request.POST.dict.side_effect = Exception("too large")
    run_init_stage(mock_request)

    # Assertions
    context: Context = get_current_context()
    assert {"key": "value"} == context.body


def test_run_init_stage_with_dict_error_and_invalid_json(mock_request):
    """Test run_init_stage with a JSON request."""
    mock_request.POST.dict.side_effect = Exception("too large")
    mock_request.body = '{"key" :: "value"}'  # Invalid json
    run_init_stage(mock_request)

    # Assertions
    context: Context = get_current_context()
    assert '{"key" :: "value"}' == context.body


def test_run_init_stage_with_complicated_json(mock_request):
    """Test run_init_stage with a JSON request."""
    mock_request.body = '        [{"a": "b"}, 20, 19, false] '
    run_init_stage(mock_request)

    # Assertions
    context: Context = get_current_context()
    assert [{"a": "b"}, 20, 19, False] == context.body


def test_run_init_stage_with_empty_body(mock_request):
    """Test run_init_stage with an empty body."""
    mock_request.POST.dict.return_value = {}
    mock_request.body = b""  # Simulate an empty body
    run_init_stage(mock_request)

    # Assertions
    context: Context = get_current_context()
    assert context.body is None


def test_run_init_stage_with_empty_body_string(mock_request):
    """Test run_init_stage with an empty body."""
    mock_request.POST.dict.return_value = {}
    mock_request.body = ""  # Simulate an empty body
    run_init_stage(mock_request)

    # Assertions
    context: Context = get_current_context()
    assert context.body is None


def test_run_init_stage_with_xml(mock_request):
    """Test run_init_stage with an XML request."""
    mock_request.content_type = "application/xml"
    mock_request.body = "<root><key>value</key></root>"  # Example XML body
    run_init_stage(mock_request)
    # Assertions
    context: Context = get_current_context()
    assert context.body == "<root><key>value</key></root>"


def test_uses_wsgi(mock_request):
    run_init_stage(mock_request)
    # Assertions
    context: Context = get_current_context()
    assert "/hello" == context.route


def test_uses_asgi_prio(mock_request):
    mock_request.scope = asgi_scope
    run_init_stage(mock_request)
    # Assertions
    context: Context = get_current_context()
    assert "/a/b/c/d" == context.route
