import pytest
from unittest.mock import MagicMock
from .run_init_stage import run_init_stage
from ...context import Context, get_current_context, current_context


@pytest.fixture
def mock_request():
    """Fixture to create a mock request object."""
    request = MagicMock()
    request.POST.dict.return_value = {}
    request.content_type = "application/json"
    request.body = '{"key": "value"}'  # Example JSON body
    request.META = {}
    return request

@pytest.fixture(autouse=True)
def run_around_tests():
    yield
    # Make sure to reset context after every test so it does not
    # interfere with other tests
    current_context.set(None)

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
    assert context.body is ""


def test_run_init_stage_with_empty_body_string(mock_request):
    """Test run_init_stage with an empty body."""
    mock_request.POST.dict.return_value = {}
    mock_request.body = ""  # Simulate an empty body
    run_init_stage(mock_request)

    # Assertions
    context: Context = get_current_context()
    assert context.body is ""


def test_run_init_stage_with_xml(mock_request):
    """Test run_init_stage with an XML request."""
    mock_request.content_type = "application/xml"
    mock_request.body = "<root><key>value</key></root>"  # Example XML body
    run_init_stage(mock_request)
    # Assertions
    context: Context = get_current_context()
    assert context.body == "<root><key>value</key></root>"
