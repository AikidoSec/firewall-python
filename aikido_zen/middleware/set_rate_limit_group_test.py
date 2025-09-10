import pytest
from aikido_zen.context import get_current_context, Context
from aikido_zen.thread.thread_cache import get_cache
from .set_rate_limit_group import set_rate_limit_group


@pytest.fixture(autouse=True)
def run_around_tests():
    get_cache().reset()
    yield
    # Reset context and cache after every test
    from aikido_zen.context import current_context

    current_context.set(None)
    get_cache().reset()


def set_context_and_lifecycle():
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
    context = Context(
        req=wsgi_request,
        body=None,
        source="flask",
    )
    context.set_as_current_context()
    return context


def test_set_rate_limit_group_valid_group_id(caplog):
    context1 = set_context_and_lifecycle()
    assert context1.rate_limit_group is None
    set_rate_limit_group("group1")
    assert context1.rate_limit_group == "group1"
    assert "Group ID cannot be empty." not in caplog.text
    assert "was called without a context" not in caplog.text
    assert "must be called before the Zen middleware is executed" not in caplog.text


def test_set_rate_limit_group_empty_group_id(caplog):
    context1 = set_context_and_lifecycle()
    assert context1.rate_limit_group is None
    set_rate_limit_group("")
    assert context1.rate_limit_group is None
    assert "Group ID cannot be empty." in caplog.text


def test_set_rate_limit_group_none_group_id(caplog):
    context1 = set_context_and_lifecycle()
    assert context1.rate_limit_group is None
    set_rate_limit_group(None)
    assert context1.rate_limit_group is None
    assert "Group ID cannot be empty." in caplog.text


def test_set_rate_limit_group_no_context(caplog):
    from aikido_zen.context import current_context

    current_context.set(None)
    set_rate_limit_group("group1")
    assert "was called without a context" in caplog.text


def test_set_rate_limit_group_middleware_already_executed(caplog):
    context1 = set_context_and_lifecycle()
    context1.executed_middleware = True
    set_rate_limit_group("group1")
    assert "must be called before the Zen middleware is executed" in caplog.text
    assert context1.rate_limit_group is "group1"


def test_set_rate_limit_group_non_string_group_id(caplog):
    context1 = set_context_and_lifecycle()
    assert context1.rate_limit_group is None
    set_rate_limit_group(123)
    assert context1.rate_limit_group == "123"


def test_set_rate_limit_group_non_string_group_id_non_number(caplog):
    context1 = set_context_and_lifecycle()
    assert context1.rate_limit_group is None
    set_rate_limit_group({"a": "b"})
    assert context1.rate_limit_group is None
    assert "Group ID must be a string or a number" in caplog.text


def test_set_rate_limit_group_overwrite_existing_group():
    context1 = set_context_and_lifecycle()
    assert context1.rate_limit_group is None
    set_rate_limit_group("group1")
    assert context1.rate_limit_group == "group1"
    set_rate_limit_group("group2")
    assert context1.rate_limit_group == "group2"
