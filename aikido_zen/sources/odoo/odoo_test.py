import io
import json
import subprocess
import sys
import types
import uuid
import xmlrpc.client
from weakref import ref

import pytest
import werkzeug.wrappers
import wrapt
from werkzeug.test import EnvironBuilder

import aikido_zen.sources.odoo as odoo_source
from aikido_zen.context import Context, current_context, get_current_context
from aikido_zen.sources.odoo.extract_request import save_route_args
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


def _sql(payload):
    return "INSERT INTO zen_dogs (dog_name, isadmin) VALUES ('%s', FALSE)" % payload


def _scan(sql, context):
    return context_contains_sql_injection(
        sql, "psycopg2.Connection.Cursor.execute", context, "postgres"
    )


@pytest.fixture
def context():
    ctx = Context(req=ENVIRON, source="odoo")
    ctx.set_as_current_context()
    yield ctx
    current_context.set(None)


def _odoo_get_json_data(self):
    return json.loads(self.httprequest.get_data(as_text=True))


def _odoo_http(missing=None):
    def method(*args, **kwargs):
        return None

    module = types.ModuleType("fake_odoo_http")
    module.Application = type("Application", (), {"__call__": method})
    module.Dispatcher = type("Dispatcher", (), {"pre_dispatch": method})
    if missing == "Dispatcher.pre_dispatch":
        module.Dispatcher = type("Dispatcher", (), {})
    module.Request = type("Request", (), {"get_json_data": _odoo_get_json_data})
    module.werkzeug = types.SimpleNamespace(
        wrappers=types.SimpleNamespace(
            Request=type("Request", (werkzeug.wrappers.Request,), {})
        )
    )
    return module


@pytest.fixture
def odoo_http():
    module = _odoo_http()
    odoo_source.patch_odoo_http(module)
    return module


@pytest.fixture
def stored_bodies(monkeypatch):
    stored = []
    set_body = Context.set_body

    def record_set_body(self, body):
        stored.append(body)
        set_body(self, body)

    monkeypatch.setattr(Context, "set_body", record_set_body)
    return stored


def _httprequest(
    module,
    data=None,
    content_type=None,
    context=None,
    key="aikido_zen.odoo_context",
    **request,
):
    environ = EnvironBuilder(
        method="POST", data=data, content_type=content_type, **request
    ).get_environ()
    environ[key] = ref(context or get_current_context())
    return module.werkzeug.wrappers.Request(environ)


def _read_json(module, body):
    request = module.Request()
    request.httprequest = _httprequest(module, body, "application/json")
    return request.get_json_data()


def test_wsgi_context_reads_the_odoo_request(context):
    assert context.source == "odoo"
    assert context.method == "POST"
    assert context.query["dog_name"] == [WSGI_PAYLOAD]
    assert context.cookies["session_id"] == "abc123"


@pytest.mark.parametrize(
    "params, path",
    [
        ({"dog_name": PAYLOAD}, ".params.dog_name"),
        ({"kwargs": {"dog_name": PAYLOAD}}, ".params.kwargs.dog_name"),
    ],
)
def test_jsonrpc_body_is_detected(context, odoo_http, params, path):
    _read_json(odoo_http, json.dumps({"jsonrpc": "2.0", "params": params}))
    found = _scan(_sql(PAYLOAD), get_current_context())

    assert (found["source"], found["pathToPayload"]) == ("body", path)
    assert found["payload"] == PAYLOAD


def test_odoos_json_is_stored_once_without_parsing_it_again(
    context, odoo_http, stored_bodies
):
    body = {"params": {"dog_name": PAYLOAD}}
    request = odoo_http.Request()
    request.httprequest = _httprequest(odoo_http, json.dumps(body), "application/json")

    request.get_json_data()
    request.get_json_data()

    assert stored_bodies == [body]


def test_json_string_holding_json_is_detected(context, odoo_http):
    _read_json(odoo_http, json.dumps(json.dumps({"dog_name": PAYLOAD})))

    assert _scan(_sql(PAYLOAD), get_current_context())["source"] == "body"


@pytest.mark.parametrize(
    "data, content_type",
    [(PAYLOAD, "text/plain"), (f'<dog name="{PAYLOAD}"/>', "application/xml")],
)
def test_raw_body_is_stored_as_read(context, odoo_http, data, content_type):
    _httprequest(odoo_http, data, content_type).get_data(as_text=True)

    assert get_current_context().body == data


def test_form_fields_and_upload_names_are_stored(context, odoo_http):
    data = {"dog_name": PAYLOAD, "photo": (io.BytesIO(b"x"), "../../etc/passwd")}

    _ = _httprequest(odoo_http, data).form

    assert get_current_context().body == {
        "dog_name": [PAYLOAD],
        "photo": ["../../etc/passwd"],
    }
    assert _scan(_sql(PAYLOAD), get_current_context())["source"] == "body"


def test_unchanged_form_is_stored_once(context, odoo_http, stored_bodies):
    httprequest = _httprequest(
        odoo_http, {"dog_name": PAYLOAD}, "application/x-www-form-urlencoded"
    )
    _ = httprequest.form

    assert httprequest.get_data() == b""
    assert httprequest.get_data() == b""
    assert stored_bodies == [{"dog_name": [PAYLOAD]}]


def test_body_of_another_request_is_not_stored(context, odoo_http):
    other = Context(req=ENVIRON, source="odoo")

    _httprequest(odoo_http, PAYLOAD, "text/plain", context=other).get_data()

    assert context.body is None
    assert other.body is None


def test_flask_request_in_the_same_process_is_not_changed(odoo_http):
    flask_context = Context(req=ENVIRON, source="flask")
    flask_context.set_as_current_context()
    upload = {"photo": (io.BytesIO(b"x"), "../../etc/passwd")}

    flask_request = _httprequest(
        odoo_http, upload, context=flask_context, key="aikido_zen.context"
    )

    _ = flask_request.form

    assert flask_context.body is None
    current_context.set(None)


def test_odoo_query_and_every_cookie_value_are_added_to_zens_parse(context, odoo_http):
    _scan("SELECT 1", context)
    httprequest = _httprequest(
        odoo_http,
        query_string={"dog_name": ODOO_PAYLOAD},
        headers={"Cookie": "session_id=odoo1; session_id=odoo2; lang=en"},
    )

    _ = httprequest.form
    updated = get_current_context()

    assert updated.query["dog_name"] == [WSGI_PAYLOAD, ODOO_PAYLOAD]
    assert updated.cookies["session_id"] == ["abc123", "odoo1", "odoo2"]
    assert updated.cookies["lang"] == "en"
    assert _scan(_sql(ODOO_PAYLOAD), updated)["source"] == "query"


class _CountingStr(str):
    comparisons = 0

    def __eq__(self, other):
        _CountingStr.comparisons += 1
        return str.__eq__(self, other)

    __hash__ = str.__hash__


def test_repeated_query_and_cookie_values_are_compared_once(context, odoo_http):
    values = [_CountingStr(i) for i in range(1000)]
    context.query = {"tag": values}
    context.cookies = {"tag": values}
    httprequest = _httprequest(
        odoo_http,
        query_string=[("tag", value) for value in reversed(values)],
        headers={"Cookie": "; ".join(f"tag={value}" for value in reversed(values))},
    )
    _CountingStr.comparisons = 0

    _ = httprequest.form

    assert _CountingStr.comparisons < 4 * len(values)


def test_route_args_are_detected_next_to_the_url_segments():
    route_context = Context(
        req={**ENVIRON, "PATH_INFO": "/zen/dog/o%27k", "QUERY_STRING": ""},
        source="odoo",
    )
    route_context.set_as_current_context()
    segments = list(route_context.route_params)
    _scan("SELECT 1", route_context)

    save_route_args({"dog_name": ODOO_PAYLOAD})
    updated = get_current_context()
    found = _scan(_sql(ODOO_PAYLOAD), updated)

    assert updated.route_params["url_segments"] == segments
    assert (found["source"], found["pathToPayload"]) == ("route_params", ".dog_name")
    current_context.set(None)


def test_only_plain_route_args_are_stored(context):
    class Record:
        def __eq__(self, other):
            raise AssertionError("comparing an Odoo record runs SQL")

        __hash__ = object.__hash__

    token = uuid.UUID("12345678-1234-5678-1234-567812345678")

    save_route_args(
        {"partner": Record(), "nested": {"value": PAYLOAD}, "page": 3, "token": token}
    )

    assert get_current_context().route_params == {"page": 3, "token": str(token)}


def _is_patched(owner, name):
    return isinstance(vars(owner).get(name), wrapt.FunctionWrapper)


def test_every_hook_is_patched_when_odoo_has_them(odoo_http):
    werkzeug_request = odoo_http.werkzeug.wrappers.Request

    assert _is_patched(odoo_http.Application, "__call__")
    assert _is_patched(odoo_http.Dispatcher, "pre_dispatch")
    assert _is_patched(odoo_http.Request, "get_json_data")
    assert _is_patched(werkzeug_request, "get_data")
    assert _is_patched(werkzeug_request, "_load_form_data")


def test_no_hook_is_patched_when_one_is_missing(caplog):
    module = _odoo_http(missing="Dispatcher.pre_dispatch")

    odoo_source.patch_odoo_http(module)

    assert not _is_patched(module.Application, "__call__")
    assert not _is_patched(module.werkzeug.wrappers.Request, "get_data")
    assert "Dispatcher.pre_dispatch" in caplog.text


def _application(monkeypatch, odoo_call, blocked=None):
    module = _odoo_http()
    module.Application.__call__ = odoo_call
    odoo_source.patch_odoo_http(module)
    monkeypatch.setattr(odoo_source, "should_block", lambda: blocked)
    return module.Application()


def test_request_runs_once_when_odoo_raises(context, monkeypatch):
    calls = []

    def odoo_call(self, environ, start_response):
        calls.append(environ)
        raise RuntimeError("database connection lost")

    application = _application(monkeypatch, odoo_call)
    with pytest.raises(RuntimeError, match="database connection lost"):
        application(dict(ENVIRON), lambda *args: None)

    assert len(calls) == 1


def test_request_environ_points_to_its_context(monkeypatch):
    seen = []

    def odoo_call(self, environ, start_response):
        seen.append(environ["aikido_zen.odoo_context"]() is get_current_context())

    _application(monkeypatch, odoo_call)(dict(ENVIRON), lambda *args: None)

    assert seen == [True]
    current_context.set(None)


def test_previous_context_is_cleared_when_zen_cannot_build_one(context, monkeypatch):
    seen = []

    def odoo_call(self, environ, start_response):
        seen.append(get_current_context())

    application = _application(monkeypatch, odoo_call)
    monkeypatch.setattr(odoo_source, "Context", lambda **kwargs: 1 / 0)
    application(dict(ENVIRON), lambda *args: None)

    assert seen == [None]


def test_blocked_request_gets_a_plain_response_without_odoo(context, monkeypatch):
    calls = []
    statuses = []

    def odoo_call(self, environ, start_response):
        calls.append(environ)

    application = _application(
        monkeypatch, odoo_call, blocked=("You are blocked by Zen.", 403)
    )
    body = application(dict(ENVIRON), lambda status, headers: statuses.append(status))

    assert b"".join(body) == b"You are blocked by Zen."
    assert statuses[0].startswith("403")
    assert calls == []


@pytest.mark.parametrize("status, status_code", [("404 NOT FOUND", 404), ("bad", 0)])
def test_post_response_gets_the_status_odoo_sent(
    context, monkeypatch, status, status_code
):
    stages = []

    def odoo_call(self, environ, start_response):
        start_response(status, [])
        return [b"ok"]

    application = _application(monkeypatch, odoo_call)
    monkeypatch.setattr(
        odoo_source.funcs, "request_handler", lambda **kwargs: stages.append(kwargs)
    )

    assert application(dict(ENVIRON), lambda *args: None) == [b"ok"]
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


def test_odoo_http_imported_before_zen_is_patched():
    script = (
        "import sys, types\n"
        "import werkzeug.wrappers\n"
        "import wrapt\n"
        "odoo_http = types.ModuleType('odoo.http')\n"
        "odoo_http.Application = type('Application', (), {'__call__': lambda s: None})\n"
        "odoo_http.Dispatcher = type('Dispatcher', (), {'pre_dispatch': lambda s: None})\n"
        "odoo_http.Request = type('Request', (), {'get_json_data': lambda s: None})\n"
        "odoo_http.werkzeug = types.SimpleNamespace(wrappers=types.SimpleNamespace("
        "Request=type('Request', (werkzeug.wrappers.Request,), {})))\n"
        "sys.modules['odoo'] = types.ModuleType('odoo')\n"
        "sys.modules['odoo.http'] = odoo_http\n"
        "import aikido_zen.sources.odoo\n"
        "print(isinstance(vars(odoo_http.Application)['__call__'], wrapt.FunctionWrapper))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True
    )
    assert result.stdout.splitlines()[-1] == "True", result.stderr


def test_odoo_import_hooks_are_registered():
    from wrapt.importer import _post_import_hooks

    assert "odoo.http" in _post_import_hooks
    assert "odoo.service.server" in _post_import_hooks
    assert "odoo.addons.base.controllers.rpc" in _post_import_hooks
    assert "odoo.addons.rpc.controllers.xmlrpc" in _post_import_hooks


def test_xmlrpc_params_replace_the_raw_xml(context, odoo_http):
    params = ("zenpoc", 2, "admin", "zen.dog", "create_unsafe", [PAYLOAD])
    httprequest = _httprequest(
        odoo_http, xmlrpc.client.dumps(params, "execute_kw"), "text/xml"
    )
    parsed, _ = xmlrpc.client.loads(httprequest.get_data())
    _scan("SELECT 1", get_current_context())

    odoo_source._dispatch_rpc(
        lambda *args: None, None, ("object", "execute_kw", parsed), {}
    )
    found = _scan(_sql(PAYLOAD), get_current_context())

    assert (found["kind"], found["source"]) == ("sql_injection", "body")


def test_jsonrpc_body_is_kept_when_dispatch_rpc_runs(context):
    body = {"params": {"service": "object", "method": "execute_kw", "args": [1]}}
    context.set_body(body)

    odoo_source._dispatch_rpc(
        lambda *args: None, None, ("object", "execute_kw", [1]), {}
    )

    assert get_current_context().body == body
