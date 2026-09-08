import pytest
from . import current_context, Context
from .set_tenant_id import set_tenant_id


@pytest.fixture(autouse=True)
def run_around_tests():
    yield
    current_context.set(None)


def _create_context():
    wsgi_request = {
        "REQUEST_METHOD": "GET",
        "HTTP_HEADER_1": "header 1 value",
        "wsgi.url_scheme": "http",
        "HTTP_HOST": "localhost:8080",
        "PATH_INFO": "/hello",
        "QUERY_STRING": "",
        "CONTENT_TYPE": "application/json",
        "REMOTE_ADDR": "198.51.100.23",
    }
    context = Context(req=wsgi_request, body=None, source="flask")
    context.set_as_current_context()
    return context


def test_set_tenant_id_string():
    ctx = _create_context()
    set_tenant_id("tenant_123")
    assert ctx.tenant_id == "tenant_123"


def test_set_tenant_id_integer():
    ctx = _create_context()
    set_tenant_id(42)
    assert ctx.tenant_id == "42"


def test_set_tenant_id_empty_string(caplog):
    ctx = _create_context()
    set_tenant_id("")
    assert ctx.tenant_id is None
    assert "non-empty" in caplog.text


def test_set_tenant_id_invalid_type(caplog):
    ctx = _create_context()
    set_tenant_id(12.34)
    assert ctx.tenant_id is None
    assert "expects a string or integer" in caplog.text


def test_set_tenant_id_none(caplog):
    ctx = _create_context()
    set_tenant_id(None)
    assert ctx.tenant_id is None
    assert "expects a string or integer" in caplog.text


def test_set_tenant_id_dict(caplog):
    ctx = _create_context()
    set_tenant_id({"id": 1})
    assert ctx.tenant_id is None
    assert "expects a string or integer" in caplog.text


def test_set_tenant_id_no_context(caplog):
    import logging

    # No context set — should not raise, tenant_id is not applied anywhere
    with caplog.at_level(logging.DEBUG, logger="Zen"):
        set_tenant_id("tenant_123")
    assert "No context set" in caplog.text


def test_set_tenant_id_overwrites():
    ctx = _create_context()
    set_tenant_id("first")
    assert ctx.tenant_id == "first"
    set_tenant_id("second")
    assert ctx.tenant_id == "second"
