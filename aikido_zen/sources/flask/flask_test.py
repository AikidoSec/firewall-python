import gc
from contextvars import copy_context
import signal
import traceback
import weakref
from io import BytesIO
from unittest.mock import patch

import pytest
from flask import (
    Flask,
    Response,
    copy_current_request_context,
    request,
    stream_with_context,
)
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.test import EnvironBuilder
from werkzeug.wsgi import ClosingIterator, FileWrapper

import aikido_zen.sources.flask as source
from aikido_zen.background_process.ipc import IPCClient
from aikido_zen.context import current_context, get_current_context
from aikido_zen.vulnerabilities.sql_injection.context_contains_sql_injection import (
    context_contains_sql_injection,
)

sample_environ = {
    "REQUEST_METHOD": "POST",
    "HTTP_HEADER_1": "header 1 value",
    "HTTP_HEADER_2": "Header 2 value",
    "RANDOM_VALUE": "Random value",
    "HTTP_COOKIE": "sessionId=abc123xyz456;",
    "wsgi.url_scheme": "https",
    "HTTP_HOST": "example.com",
    "PATH_INFO": "/hello",
    "QUERY_STRING": "user=JohnDoe&age=30&age=35",
    "body": "username=JohnDoe&age=30&age=35",
    "CONTENT_TYPE": "application/x-www-form-urlencoded",
    "REMOTE_ADDR": "198.51.100.23",
}

sample_environ_malformed_cookie = {
    "REQUEST_METHOD": "POST",
    "HTTP_HEADER_1": "header 1 value",
    "HTTP_HEADER_2": "Header 2 value",
    "RANDOM_VALUE": "Random value",
    "HTTP_COOKIE": "\u0000" * 10,
    "wsgi.url_scheme": "https",
    "HTTP_HOST": "example.com",
    "PATH_INFO": "/hello",
    "QUERY_STRING": "user=JohnDoe&age=30&age=35",
    "body": '{"asd": 1}',
    "CONTENT_TYPE": "application/x-www-form-urlencoded",
    "REMOTE_ADDR": "198.51.100.23",
}

sample_environ_malformed_json = {
    "REQUEST_METHOD": "POST",
    "HTTP_HEADER_1": "header 1 value",
    "HTTP_HEADER_2": "Header 2 value",
    "RANDOM_VALUE": "Random value",
    "HTTP_COOKIE": "sessionId=abc123xyz456;",
    "wsgi.url_scheme": "https",
    "HTTP_HOST": "example.com",
    "PATH_INFO": "/hello",
    "body": '{"asd": 1invalidjson}',
    "QUERY_STRING": "user=JohnDoe",
    "CONTENT_TYPE": "application/json",
    "REMOTE_ADDR": "198.51.100.23",
}

sample_environ_view_args_and_malformed_json = {
    "REQUEST_METHOD": "POST",
    "HTTP_COOKIE": "sessionId=abc123xyz456;",
    "HTTP_HEADER_1": "header 1 value",
    "HTTP_HEADER_2": "Header 2 value",
    "HTTP_HOST": "example.com",
    "CONTENT_TYPE": "application/json",
    "PATH_INFO": "/hello/JohnDoe/30",
    "QUERY_STRING": "",
    "body": '{"invalid_json": true',
    "REMOTE_ADDR": "198.51.100.23",
    "wsgi.url_scheme": "https",
}


class TimeoutException(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutException


signal.signal(signal.SIGALRM, timeout_handler)


def test_flask_all_3_func_with_view_args_and_invalid_json_body():
    with patch(
        "aikido_zen.sources.functions.request_handler.request_handler"
    ) as mock_request_handler:
        IPCClient.reset()
        current_context.set(None)
        mock_request_handler.return_value = None

        from flask import Flask

        app = Flask(__name__)

        @app.route("/hello/<user>/<age>", methods=["POST"])
        def hello(user, age):
            return f"User: {user}, Age: {age}"

        try:
            signal.alarm(1)

            app(sample_environ_view_args_and_malformed_json, lambda x, y: x)
            app.run()

        except TimeoutException:
            pass

        assert get_current_context().method == "POST"
        assert get_current_context().body is None
        assert get_current_context().headers == {
            "COOKIE": ["sessionId=abc123xyz456;"],
            "HEADER_1": ["header 1 value"],
            "HEADER_2": ["Header 2 value"],
            "HOST": ["example.com"],
            "CONTENT_TYPE": ["application/json"],
        }
        calls = mock_request_handler.call_args_list
        assert len(calls) == 2
        assert calls[0][1]["stage"] == "init"
        assert calls[1][1]["stage"] == "post_response"
        assert calls[1][1]["status_code"] == 200

        assert get_current_context().route_params["user"] == "JohnDoe"
        assert get_current_context().route_params["age"] == "30"


def test_flask_all_3_func_with_malformed_cookie():
    """When the flask body can not be parsed (because it contains invalid json for example), we should still parse the cookies of the endpoint"""
    with patch(
        "aikido_zen.sources.functions.request_handler.request_handler"
    ) as mock_request_handler:
        IPCClient.reset()
        current_context.set(None)
        mock_request_handler.return_value = None

        from flask import Flask

        app = Flask(__name__)
        try:
            signal.alarm(1)
            app(sample_environ_malformed_cookie, lambda x, y: x)
            app.run()
        except TimeoutException:
            pass

        print(get_current_context())

        assert get_current_context().method == "POST"
        assert get_current_context().cookies == {"\u0000" * 10: ""}

        calls = mock_request_handler.call_args_list
        assert len(calls) == 2
        assert calls[0][1]["stage"] == "init"
        assert calls[1][1]["stage"] == "post_response"
        assert calls[1][1]["status_code"] == 404


def test_flask_all_3_func_with_invalid_body():
    """When the flask body can not be parsed (because it contains invalid json for example), we should still parse the cookies of the endpoint"""
    with patch(
        "aikido_zen.sources.functions.request_handler.request_handler"
    ) as mock_request_handler:
        IPCClient.reset()
        current_context.set(None)
        mock_request_handler.return_value = None

        from flask import Flask

        app = Flask(__name__)
        try:
            signal.alarm(1)
            app(sample_environ_malformed_json, lambda x, y: x)
            app.run()
        except TimeoutException:
            pass

        assert get_current_context().method == "POST"
        assert (
            get_current_context().body == None
        )  # body is None since it's invalid json
        assert get_current_context().headers == {
            "COOKIE": ["sessionId=abc123xyz456;"],
            "HEADER_1": ["header 1 value"],
            "HEADER_2": ["Header 2 value"],
            "HOST": ["example.com"],
            "CONTENT_TYPE": ["application/json"],
        }
        calls = mock_request_handler.call_args_list
        assert len(calls) == 2
        assert calls[0][1]["stage"] == "init"
        assert calls[1][1]["stage"] == "post_response"
        assert calls[1][1]["status_code"] == 404


def test_flask_all_3_func():
    with patch(
        "aikido_zen.sources.functions.request_handler.request_handler"
    ) as mock_request_handler:
        IPCClient.reset()
        current_context.set(None)
        mock_request_handler.return_value = None

        from flask import Flask

        app = Flask(__name__)
        try:
            signal.alarm(1)
            app(sample_environ, lambda x, y: x)
            app.run()
        except TimeoutException:
            pass
        assert get_current_context().method == "POST"
        assert get_current_context().body == None
        assert get_current_context().headers == {
            "COOKIE": ["sessionId=abc123xyz456;"],
            "HEADER_1": ["header 1 value"],
            "HEADER_2": ["Header 2 value"],
            "HOST": ["example.com"],
            "CONTENT_TYPE": ["application/x-www-form-urlencoded"],
        }
        calls = mock_request_handler.call_args_list
        assert len(calls) == 2
        assert calls[0][1]["stage"] == "init"
        assert calls[1][1]["stage"] == "post_response"
        assert calls[1][1]["status_code"] == 404


def test_startup_flask():
    IPCClient.reset()
    from flask import Flask

    app = Flask(__name__)
    try:
        signal.alarm(1)
        app.run()
    except TimeoutException:
        pass


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(source, "should_block", lambda: None)
    monkeypatch.setattr(source.funcs, "request_handler", lambda **kwargs: None)
    current_context.set(None)
    yield Flask(__name__)
    current_context.set(None)


@pytest.fixture
def without_gc():
    enabled = gc.isenabled()
    gc.collect()
    gc.disable()
    try:
        yield
    finally:
        if enabled:
            gc.enable()
        gc.collect()


@pytest.mark.parametrize("status", [404, 405, 308])
@pytest.mark.parametrize("custom_handler", [False, True])
def test_routing_requests_release_cached_bodies_without_gc(
    app, without_gc, status, custom_handler
):
    refs = []
    app.add_url_rule("/known", endpoint="known", view_func=lambda: "ok")
    app.add_url_rule(
        "/slash/", endpoint="slash", view_func=lambda: "ok", methods=["POST"]
    )
    if custom_handler:
        app.register_error_handler(HTTPException, lambda error: ("handled", error.code))

    @app.before_request
    def capture():
        refs.append(weakref.ref(request._get_current_object()))
        assert get_current_context().body == "x" * 1024 * 1024

    path = {404: "/missing", 405: "/known", 308: "/slash"}[status]
    client = app.test_client()
    for _ in range(3):
        response = client.post(
            path, data=b"x" * 1024 * 1024, content_type="application/octet-stream"
        )
        assert response.status_code == status
        response.close()
        del response

    assert all(ref() is None for ref in refs)


@pytest.mark.parametrize("status", [404, 405])
def test_custom_handlers_and_teardown_keep_body_inspection(app, without_gc, status):
    attack = "Malicious Pet', 'Gru from the Minions') --"
    payload = {"name": attack}
    refs = []
    stages = []
    app.add_url_rule("/known", view_func=lambda: "ok")

    def inspect_body():
        assert get_current_context().body == payload
        assert request.get_json() == payload
        result = context_contains_sql_injection(
            sql=f"INSERT INTO pets(name) VALUES ('{attack}')",
            operation="psycopg2.Cursor.execute",
            context=get_current_context(),
            dialect="postgres",
        )
        assert result["source"] == "body"
        assert result["payload"] == attack
        assert request.routing_exception.__traceback__ is not None

    @app.errorhandler(HTTPException)
    def handler(error):
        refs.append(weakref.ref(request._get_current_object()))
        inspect_body()
        stages.append("handler")
        return "handled", error.code

    @app.teardown_request
    def teardown(error):
        inspect_body()
        stages.append("teardown")

    response = app.test_client().post(
        "/missing" if status == 404 else "/known", json=payload
    )
    assert response.status_code == status
    assert response.data == b"handled"
    response.close()
    del response

    assert stages == ["handler", "teardown"]
    assert refs[0]() is None


def test_custom_flask_error_override_keeps_body_and_releases_request(app, without_gc):
    refs = []
    payload = {"name": "value"}

    class CustomFlask(Flask):
        def handle_http_exception(self, error):
            refs.append(weakref.ref(request._get_current_object()))
            assert get_current_context().body == payload
            assert request.get_json() == payload
            return self.make_response(("handled", error.code))

    response = CustomFlask(__name__).test_client().post("/missing", json=payload)
    assert response.status_code == 404
    response.close()
    del response
    assert refs[0]() is None


@pytest.mark.parametrize("finish_stream", [False, True])
def test_streamed_error_response_keeps_body_until_stream_closes(
    app, without_gc, finish_stream
):
    refs = []
    stages = []
    payload = {"name": "value"}

    @app.errorhandler(404)
    def handler(error):
        refs.append(weakref.ref(request._get_current_object()))

        @stream_with_context
        def generate():
            try:
                for part in (b"first", b"second"):
                    assert get_current_context().body == payload
                    assert request.get_json() == payload
                    assert error.__traceback__ is not None
                    stages.append(part)
                    yield part
            finally:
                assert get_current_context().body == payload
                assert request.get_json() == payload

        return Response(generate(), status=404)

    response = app.test_client().post("/missing", json=payload, buffered=False)
    assert response.status_code == 404
    assert refs[0]() is not None
    if finish_stream:
        assert b"".join(response.response) == b"firstsecond"
    response.close()
    del response

    assert stages == ([b"first", b"second"] if finish_stream else [b"first"])
    assert refs[0]() is None


def test_routing_exception_raised_by_stream_keeps_its_diagnostic_chain(app):
    @app.errorhandler(404)
    def handler(error):
        def generate():
            yield b"first"
            raise error

        return Response(generate(), status=404)

    response = app.test_client().post("/missing", json={"name": "value"})
    with pytest.raises(NotFound) as raised:
        try:
            b"".join(response.response)
        finally:
            response.close()
    assert raised.value.__traceback__ is not None
    assert raised.value.__context__ is not None


def test_copied_request_context_can_read_body_after_original_request_closes(app):
    callbacks = []
    payload = {"name": "value"}

    @app.errorhandler(404)
    def handler(error):
        @copy_current_request_context
        def later():
            return request.get_json()

        callbacks.append(later)
        return "handled", 404

    response = app.test_client().post("/missing", json=payload)
    response.close()
    assert callbacks.pop()() == payload


def test_propagating_routing_exception_keeps_its_diagnostic_chain(app):
    app.config.update(TESTING=True, TRAP_HTTP_EXCEPTIONS=True)

    with pytest.raises(NotFound) as raised:
        app.test_client().post("/missing", json={"name": "value"})

    assert raised.value.__context__ is not None
    functions = []
    trace = raised.value.__traceback__
    while trace is not None:
        functions.append(trace.tb_frame.f_code.co_name)
        trace = trace.tb_next
    assert "dispatch_request" in functions
    assert "match_request" in functions


def test_request_close_still_closes_uploaded_files(app):
    files = []

    @app.errorhandler(404)
    def handler(error):
        assert get_current_context().body.getlist("name") == ["upload"]
        files.append(request.files["file"])
        assert files[0].read() == b"x" * 1024 * 1024
        return "handled", 404

    response = app.test_client().post(
        "/missing",
        data={"name": "upload", "file": (BytesIO(b"x" * 1024 * 1024), "file.bin")},
    )
    assert response.status_code == 404
    response.close()
    assert files[0].closed


@pytest.mark.parametrize("missing_route", [False, True])
def test_handled_server_errors_release_bodies_and_preserve_tracebacks(
    app, without_gc, missing_route
):
    refs = []
    errors = []
    formatted = []
    payload = {"name": "value"}
    app.logger.disabled = True

    @app.before_request
    def capture():
        refs.append(weakref.ref(request._get_current_object()))
        assert get_current_context().body == payload
        if missing_route:
            raise ValueError("application error")

    @app.post("/error")
    def view():
        assert request.get_json() == payload
        try:
            fail()
        except LookupError as cause:
            raise ValueError("application error") from cause

    def fail():
        local_request = request._get_current_object()
        assert local_request.get_json() == payload
        raise LookupError("inner error")

    @app.errorhandler(500)
    def handler(error):
        original = error.original_exception
        errors.append(original)
        formatted.append(
            traceback.format_exception(type(original), original, original.__traceback__)
        )
        assert get_current_context().body == payload
        return "handled", 500

    response = app.test_client().post(
        "/missing" if missing_route else "/error", json=payload
    )
    assert response.status_code == 500
    response.close()
    del response

    assert refs[0]() is None
    error = errors[0]
    assert error.__traceback__ is not None
    assert (
        traceback.format_exception(type(error), error, error.__traceback__)
        == formatted[0]
    )


@pytest.mark.parametrize("status", [200, 404, 500])
def test_response_close_releases_sdk_context_without_another_request(app, status):
    refs = []
    payload = {"name": "value"}
    app.logger.disabled = True

    @app.before_request
    def capture():
        refs.append(weakref.ref(get_current_context()))
        assert get_current_context().body == payload

    @app.post("/body")
    def view():
        if status == 500:
            raise ValueError("application error")
        return "ok"

    response = app.test_client().post(
        "/missing" if status == 404 else "/body", json=payload
    )
    assert response.status_code == status
    assert get_current_context().body == payload
    response.close()
    assert get_current_context() is None
    assert refs[0]() is None


def test_late_stream_close_callbacks_keep_body_inspection_until_finished(app):
    payload = {"name": "value"}
    closed = []

    @app.post("/body")
    def view():
        def on_close():
            assert get_current_context().body == payload
            closed.append(True)

        def generate():
            response.call_on_close(on_close)
            assert get_current_context().body == payload
            yield b"ok"

        response = Response(generate())
        return response

    response = app.test_client().post("/body", json=payload, buffered=False)
    assert response.data == b"ok"
    response.close()
    assert closed == [True]
    assert get_current_context() is None


def test_response_close_preserves_another_context(app):
    @app.post("/body")
    def view():
        return "ok"

    response = app.test_client().post("/body", json={"name": "value"})
    other = source.Context(body={"name": "other"})
    other.set_as_current_context()
    response.close()
    assert get_current_context() is other


def test_response_close_preserves_application_copies_of_context(app):
    copies = []
    payload = {"name": "value"}

    @app.post("/body")
    def view():
        copies.append(copy_context())
        return "ok"

    response = app.test_client().post("/body", json=payload)
    response.close()
    assert get_current_context() is None
    assert copies[0].run(get_current_context).body == payload


def test_propagating_application_error_releases_sdk_context(app):
    app.config["TESTING"] = True

    @app.post("/body")
    def view():
        raise ValueError("application error")

    with pytest.raises(ValueError):
        app.test_client().post("/body", json={"name": "value"})
    assert get_current_context() is None


def test_bodyless_file_response_keeps_wsgi_file_wrapper(app):
    @app.get("/file")
    def view():
        return Response(FileWrapper(BytesIO(b"file data")), direct_passthrough=True)

    builder = EnvironBuilder(path="/file")
    try:
        response = app(builder.get_environ(), lambda status, headers: None)
        assert isinstance(response, FileWrapper)
        assert b"".join(response) == b"file data"
        response.close()
    finally:
        builder.close()


def test_wsgi_middleware_close_callbacks_keep_body_inspection(app):
    payload = {"name": "value"}
    closed = []
    original = app.wsgi_app

    def middleware(environ, start_response):
        def on_close():
            assert get_current_context().body == payload
            closed.append(True)

        return ClosingIterator(original(environ, start_response), on_close)

    app.wsgi_app = middleware

    @app.post("/body")
    def view():
        return "ok"

    response = app.test_client().post("/body", json=payload)
    response.close()
    assert closed == [True]
    assert get_current_context() is None
