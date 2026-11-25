import types
import uuid

import pytest
import wrapt

import aikido_zen.sources.odoo as odoo_source
from aikido_zen.context import Context, current_context, get_current_context
from aikido_zen.sources.odoo.extract_request import save_parsed_request, save_route_args
from aikido_zen.vulnerabilities.sql_injection.context_contains_sql_injection import (
    context_contains_sql_injection,
)

PAYLOAD = "Dangerous Bobby', TRUE); -- "
WSGI_PAYLOAD = "wsgi', TRUE); -- "
ODOO_PAYLOAD = "odoo', TRUE); -- "

ENVIRON = {
    "REQUEST_METHOD": "POST",
    "HTTP_HEADER_1": "header 1 value",
    "HTTP_COOKIE": "session_id=abc123;",
    "wsgi.url_scheme": "http",
    "HTTP_HOST": "localhost:8069",
    "PATH_INFO": "/zen/dog",
    "QUERY_STRING": "dog_name=wsgi%27%2C%20TRUE)%3B%20--%20",
    "CONTENT_TYPE": "application/json",
    "REMOTE_ADDR": "198.51.100.23",
}


class _Mapping:
    def __init__(self, values, flat_lists=True):
        self.values = values
        self.flat_lists = flat_lists

    def to_dict(self, flat=True):
        if flat or not self.flat_lists:
            return dict(self.values)
        return {key: [value] for key, value in self.values.items()}


class _HttpRequest:
    def __init__(self, args=None, cookies=None, form=None, files=None):
        self.args = args if args is not None else _Mapping({})
        self.cookies = (
            cookies if cookies is not None else _Mapping({}, flat_lists=False)
        )
        self.form = form
        self.files = files


def _sql(payload):
    return "INSERT INTO zen_dogs (dog_name, isadmin) VALUES ('%s', FALSE)" % payload


def _scan(sql, context):
    return context_contains_sql_injection(
        sql,
        "psycopg2.Connection.Cursor.execute",
        context,
        "postgres",
    )


@pytest.fixture
def context():
    ctx = Context(req=ENVIRON, source="odoo")
    ctx.set_as_current_context()
    yield ctx
    current_context.set(None)


def test_wsgi_context_reads_the_odoo_request(context):
    assert context.source == "odoo"
    assert context.method == "POST"
    assert context.query["dog_name"] == [WSGI_PAYLOAD]
    assert context.cookies["session_id"] == "abc123"


def test_jsonrpc_body_is_detected_in_interpolated_sql(context):
    save_parsed_request(
        _HttpRequest(),
        body={
            "jsonrpc": "2.0",
            "method": "call",
            "params": {"dog_name": PAYLOAD},
            "id": 1,
        },
    )
    found = _scan(_sql(PAYLOAD), get_current_context())
    assert found["kind"] == "sql_injection"
    assert found["source"] == "body"
    assert found["pathToPayload"] == ".params.dog_name"
    assert found["payload"] == PAYLOAD


def test_parameterized_sql_is_not_detected(context):
    save_parsed_request(
        _HttpRequest(),
        body={"params": {"dog_name": PAYLOAD}},
    )
    found = _scan(
        "INSERT INTO zen_dogs (dog_name, isadmin) VALUES (%s, FALSE)",
        get_current_context(),
    )
    assert found == {}


def test_nested_web_client_params_are_detected(context):
    save_parsed_request(
        _HttpRequest(),
        body={"params": {"kwargs": {"dog_name": PAYLOAD}}},
    )
    found = _scan(_sql(PAYLOAD), get_current_context())
    assert found["kind"] == "sql_injection"
    assert found["pathToPayload"] == ".params.kwargs.dog_name"


def test_framework_query_is_kept_after_an_earlier_scan(context):
    assert _scan(_sql(WSGI_PAYLOAD), context)["kind"] == "sql_injection"
    save_parsed_request(
        _HttpRequest(args=_Mapping({"dog_name": ODOO_PAYLOAD})),
        body={"params": {}},
    )
    updated = get_current_context()
    assert _scan(_sql(WSGI_PAYLOAD), updated)["kind"] == "sql_injection"
    assert _scan(_sql(ODOO_PAYLOAD), updated)["source"] == "query"


def test_parsing_the_same_request_again_keeps_the_cached_strings(context):
    save_parsed_request(_HttpRequest(), body={"params": {"dog_name": ODOO_PAYLOAD}})
    _scan("SELECT 1", context)
    cached = dict(context.parsed_userinput)

    save_parsed_request(_HttpRequest(), body={"params": {"dog_name": ODOO_PAYLOAD}})

    assert "body" in cached
    assert context.parsed_userinput == cached


def test_changed_body_is_scanned_after_an_earlier_scan(context):
    save_parsed_request(_HttpRequest(), body={"params": {"dog_name": "Bobby"}})
    assert _scan(_sql(PAYLOAD), context) == {}

    save_parsed_request(_HttpRequest(), body={"params": {"dog_name": PAYLOAD}})

    assert _scan(_sql(PAYLOAD), get_current_context())["source"] == "body"


def test_form_body_is_detected(context):
    save_parsed_request(
        _HttpRequest(form=_Mapping({"dog_name": PAYLOAD})),
        include_form=True,
    )
    found = _scan(_sql(PAYLOAD), get_current_context())
    assert found["kind"] == "sql_injection"
    assert found["source"] == "body"


def test_route_args_are_detected(context):
    save_route_args({"dog_name": PAYLOAD})
    found = _scan(_sql(PAYLOAD), get_current_context())
    assert found["kind"] == "sql_injection"
    assert found["source"] == "route_params"
    assert found["pathToPayload"] == ".dog_name"


def _route_context(path):
    ctx = Context(req={**ENVIRON, "PATH_INFO": path, "QUERY_STRING": ""}, source="odoo")
    ctx.set_as_current_context()
    return ctx


def test_route_args_are_detected_when_the_url_has_suspicious_segments(context):
    route_payload = "x;', TRUE) -- "
    route_context = _route_context("/zen/owner/o%27k/x;%27%2C%20TRUE)%20--%20")
    assert isinstance(route_context.route_params, list)

    save_route_args({"owner": "o'k", "dog_name": route_payload})
    found = _scan(_sql(route_payload), get_current_context())

    assert found["kind"] == "sql_injection"
    assert found["source"] == "route_params"
    assert found["pathToPayload"] == ".dog_name"


def test_url_segments_are_kept_next_to_the_route_args(context):
    route_context = _route_context("/zen/dog/o%27k")
    segments = list(route_context.route_params)

    save_route_args({"dog_name": "o'k"})

    assert get_current_context().route_params["url_segments"] == segments


def test_framework_cookies_are_kept_after_an_earlier_scan(context):
    assert _scan(_sql("abc123"), context) == {}
    save_parsed_request(
        _HttpRequest(cookies=_Mapping({"dog_name": ODOO_PAYLOAD}, flat_lists=False)),
        body={"params": {}},
    )
    found = _scan(_sql(ODOO_PAYLOAD), get_current_context())
    assert found["kind"] == "sql_injection"
    assert found["source"] == "cookies"


def test_route_args_are_kept_after_an_earlier_scan(context):
    route_context = _route_context("/zen/dog/o%27k")
    _scan("SELECT 1", route_context)
    assert route_context.parsed_userinput["route_params"]

    save_route_args({"dog_name": ODOO_PAYLOAD})
    found = _scan(_sql(ODOO_PAYLOAD), get_current_context())

    assert found["kind"] == "sql_injection"
    assert found["source"] == "route_params"


def test_record_route_args_are_not_stored(context):
    class Record:
        def __eq__(self, other):
            raise AssertionError("comparing an Odoo record runs SQL")

        __hash__ = object.__hash__

    save_route_args(
        {
            "partner": Record(),
            "nested": {"value": PAYLOAD},
            "dog_name": PAYLOAD,
            "page": 3,
            "published": True,
        }
    )

    route_params = get_current_context().route_params
    assert "partner" not in route_params
    assert "nested" not in route_params
    assert route_params["dog_name"] == PAYLOAD
    assert route_params["page"] == 3
    assert route_params["published"] is True


def test_uuid_route_args_are_stored_as_text(context):
    value = uuid.UUID("12345678-1234-5678-1234-567812345678")

    save_route_args({"token": value})

    assert get_current_context().route_params["token"] == str(value)


def _odoo_http(missing=None):
    def method(*args, **kwargs):
        return None

    classes = {
        "Application": ["__call__"],
        "Dispatcher": ["pre_dispatch"],
        "Request": ["get_json_data", "get_http_params"],
    }
    module = types.ModuleType("fake_odoo_http")
    for class_name, methods in classes.items():
        attrs = {name: method for name in methods if f"{class_name}.{name}" != missing}
        setattr(module, class_name, type(class_name, (), attrs))
    return module


def _is_patched(module, class_name, method_name):
    method = vars(getattr(module, class_name)).get(method_name)
    return isinstance(method, wrapt.FunctionWrapper)


def test_every_hook_is_patched_when_odoo_has_them():
    module = _odoo_http()

    odoo_source.patch_odoo_http(module)

    assert _is_patched(module, "Application", "__call__")
    assert _is_patched(module, "Dispatcher", "pre_dispatch")
    assert _is_patched(module, "Request", "get_json_data")
    assert _is_patched(module, "Request", "get_http_params")


def test_no_hook_is_patched_when_one_is_missing(caplog):
    module = _odoo_http(missing="Request.get_json_data")

    odoo_source.patch_odoo_http(module)

    assert not _is_patched(module, "Application", "__call__")
    assert not _is_patched(module, "Dispatcher", "pre_dispatch")
    assert not _is_patched(module, "Request", "get_http_params")
    assert "Request.get_json_data" in caplog.text


def test_request_runs_once_when_odoo_raises(context, monkeypatch):
    calls = []

    def odoo_call(self, environ, start_response):
        calls.append(environ)
        raise RuntimeError("database connection lost")

    module = _odoo_http()
    module.Application.__call__ = odoo_call
    odoo_source.patch_odoo_http(module)
    monkeypatch.setattr(odoo_source, "should_block", lambda: None)

    with pytest.raises(RuntimeError, match="database connection lost"):
        module.Application()(ENVIRON, lambda *args: None)

    assert len(calls) == 1


def test_blocked_request_gets_a_plain_response_without_odoo(context, monkeypatch):
    calls = []
    statuses = []

    def odoo_call(self, environ, start_response):
        calls.append(environ)

    module = _odoo_http()
    module.Application.__call__ = odoo_call
    odoo_source.patch_odoo_http(module)
    monkeypatch.setattr(
        odoo_source, "should_block", lambda: ("You are blocked by Zen.", 403)
    )

    body = module.Application()(
        ENVIRON, lambda status, headers: statuses.append(status)
    )

    assert body == [b"You are blocked by Zen."]
    assert statuses == ["403 Forbidden"]
    assert calls == []


@pytest.mark.parametrize("status, status_code", [("404 NOT FOUND", 404), ("bad", 0)])
def test_post_response_gets_the_status_odoo_sent(
    context, monkeypatch, status, status_code
):
    stages = []

    def odoo_call(self, environ, start_response):
        start_response(status, [])
        return [b"ok"]

    module = _odoo_http()
    module.Application.__call__ = odoo_call
    odoo_source.patch_odoo_http(module)
    monkeypatch.setattr(odoo_source, "should_block", lambda: None)
    monkeypatch.setattr(
        odoo_source.funcs, "request_handler", lambda **kwargs: stages.append(kwargs)
    )

    assert module.Application()(ENVIRON, lambda *args: None) == [b"ok"]
    assert stages == [
        {"stage": "init"},
        {"stage": "post_response", "status_code": status_code},
    ]


def test_prefork_worker_starts_zen(monkeypatch):
    import aikido_zen

    started = []
    monkeypatch.setattr(aikido_zen, "protect", lambda: started.append(True))

    assert odoo_source._worker_http_start(lambda: "running", None, (), {}) == "running"
    assert started == [True]


def test_odoo_http_import_hook_is_registered():
    import aikido_zen.sources.odoo
    from wrapt.importer import _post_import_hooks

    assert "odoo.http" in _post_import_hooks
    assert "odoo.service.server" in _post_import_hooks
    assert "odoo.addons.base.controllers.rpc" in _post_import_hooks
    assert "odoo.addons.rpc.controllers.xmlrpc" in _post_import_hooks


def test_xmlrpc_params_are_detected(context):
    params = ("zenpoc", 2, "admin", "zen.dog", "create_unsafe", [PAYLOAD])

    odoo_source._dispatch_rpc(
        lambda *args: None, None, ("object", "execute_kw", params), {}
    )
    found = _scan(_sql(PAYLOAD), get_current_context())

    assert found["kind"] == "sql_injection"
    assert found["source"] == "body"


def test_jsonrpc_body_is_kept_when_dispatch_rpc_runs(context):
    body = {"params": {"service": "object", "method": "execute_kw", "args": [1]}}
    context.set_body(body)

    odoo_source._dispatch_rpc(
        lambda *args: None, None, ("object", "execute_kw", [1]), {}
    )

    assert get_current_context().body == body
