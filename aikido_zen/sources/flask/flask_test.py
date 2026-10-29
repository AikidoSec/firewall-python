import pytest
import signal
from io import BytesIO

from flask import Flask, request, signals
from werkzeug.exceptions import HTTPException
from unittest.mock import patch
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


class CountingInput(BytesIO):
    reads = 0

    def read(self, *args, **kwargs):
        self.reads += 1
        return super().read(*args, **kwargs)

    def readinto(self, *args, **kwargs):
        self.reads += 1
        return super().readinto(*args, **kwargs)


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(source, "should_block", lambda: None)
    monkeypatch.setattr(source.funcs, "request_handler", lambda **kwargs: None)
    current_context.set(None)
    yield Flask(__name__)
    current_context.set(None)


@pytest.mark.parametrize("status", [404, 405])
def test_default_routing_rejection_does_not_read_body(app, status, monkeypatch):
    stages = []
    monkeypatch.setattr(
        source.funcs, "request_handler", lambda **kwargs: stages.append(kwargs)
    )
    app.add_url_rule("/known", view_func=lambda: "ok")
    stream = CountingInput(b"x" * 24 * 1024 * 1024)
    path = "/missing" if status == 404 else "/known"
    response = app.test_client(use_cookies=False).post(
        path + "?name=value",
        input_stream=stream,
        content_type="application/octet-stream",
        headers={"Cookie": "name=value"},
    )
    assert response.status_code == status
    assert stream.reads == 0
    context = get_current_context()
    assert context.body is None
    assert context.query == {"name": ["value"]}
    assert context.cookies == {"name": "value"}
    assert context.method == "POST"
    assert stages == [
        {"stage": "init"},
        {"stage": "post_response", "status_code": status},
    ]
    response.close()


def test_matched_route_still_captures_body_before_application_reads(app):
    @app.post("/body")
    def view():
        assert get_current_context().body == {"name": "value"}
        assert request.get_json() == {"name": "value"}
        return "ok"

    response = app.test_client().post("/body", json={"name": "value"})
    assert response.status_code == 200
    response.close()


def test_skipping_unused_body_keeps_attack_wave_detection(app, monkeypatch):
    from aikido_zen.vulnerabilities.attack_wave_detection.attack_wave_detector import (
        AttackWaveDetector,
    )

    detector = AttackWaveDetector(attack_wave_threshold=2)
    results = []

    def handle(stage, status_code=0):
        if stage == "post_response":
            results.append(detector.is_attack_wave(get_current_context(), status_code))

    monkeypatch.setattr(source.funcs, "request_handler", handle)
    client = app.test_client()
    for _ in range(2):
        response = client.post("/.env", data=b"body")
        assert response.status_code == 404
        assert get_current_context().body is None
        response.close()
    assert results == [False, True]


@pytest.mark.parametrize(
    "hook",
    [
        "before_request",
        "url_value_preprocessor",
        "after_request",
        "teardown_request",
        "teardown_appcontext",
    ],
)
def test_routing_rejections_keep_body_available_to_application_hooks(app, hook):
    captured = []

    def callback(*args):
        captured.append(get_current_context().body)
        if hook == "after_request":
            return args[0]

    getattr(app, hook)(callback)
    response = app.test_client().post("/missing", json={"name": "value"})
    assert response.status_code == 404
    response.close()
    assert captured == [{"name": "value"}]


@pytest.mark.parametrize("status", [404, 405])
@pytest.mark.parametrize("handler_type", ["code", "http_exception", "exception"])
def test_custom_routing_error_handler_keeps_body_inspection(app, status, handler_type):
    attack = "Malicious Pet', 'Gru from the Minions') --"
    app.add_url_rule("/known", view_func=lambda: "ok")

    def handler(error):
        result = context_contains_sql_injection(
            sql=f"INSERT INTO pets(name) VALUES ('{attack}')",
            operation="psycopg2.Cursor.execute",
            context=get_current_context(),
            dialect="postgres",
        )
        assert result["source"] == "body"
        assert result["payload"] == attack
        assert request.get_json() == {"name": attack}
        return "handled", error.code

    error = {"code": status, "http_exception": HTTPException, "exception": Exception}[
        handler_type
    ]
    app.register_error_handler(error, handler)
    path = "/missing" if status == 404 else "/known"
    response = app.test_client().post(path, json={"name": attack})
    assert response.status_code == status
    assert response.data == b"handled"
    response.close()


def test_unrelated_error_handlers_do_not_force_body_capture(app):
    app.register_error_handler(500, lambda error: ("server error", 500))
    app.register_error_handler(ValueError, lambda error: ("value error", 400))
    stream = CountingInput(b"body")
    response = app.test_client().post("/missing", input_stream=stream)
    assert response.status_code == 404
    assert stream.reads == 0
    assert get_current_context().body is None
    response.close()


def test_trapped_routing_error_keeps_body_for_server_error_handler(app):
    app.config["TRAP_HTTP_EXCEPTIONS"] = True
    captured = []

    def handler(error):
        captured.append(get_current_context().body)
        return "handled", 500

    app.register_error_handler(500, handler)
    response = app.test_client().post("/missing", json={"name": "value"})
    assert response.status_code == 500
    assert response.data == b"handled"
    assert captured == [{"name": "value"}]
    response.close()


def test_before_request_can_handle_unmatched_request_with_body(app):
    @app.before_request
    def handle():
        assert get_current_context().body == {"name": "value"}
        assert request.get_json() == {"name": "value"}
        return "handled"

    response = app.test_client().post("/missing", json={"name": "value"})
    assert response.status_code == 200
    assert response.data == b"handled"
    response.close()


@pytest.mark.parametrize(
    "name",
    [
        "request_started",
        "request_finished",
        "request_tearing_down",
        "appcontext_tearing_down",
        "appcontext_popped",
    ],
)
def test_routing_rejections_keep_body_available_to_signal_receivers(app, name):
    pytest.importorskip("blinker")
    captured = []

    def receiver(sender, **kwargs):
        captured.append(get_current_context().body)

    signal = getattr(signals, name)
    with signal.connected_to(receiver, app):
        response = app.test_client().post("/missing", json={"name": "value"})
        assert response.status_code == 404
        response.close()
    assert captured == [{"name": "value"}]


def test_matched_route_returning_404_keeps_existing_body_capture(app):
    @app.post("/body")
    def view():
        assert get_current_context().body == {"name": "value"}
        return "missing", 404

    response = app.test_client().post("/body", json={"name": "value"})
    assert response.status_code == 404
    response.close()


def test_custom_error_handler_keeps_multipart_files_and_fields(app):
    @app.errorhandler(404)
    def handler(error):
        assert get_current_context().body.getlist("name") == ["upload"]
        assert len(request.files["file"].read()) == 10 * 1024 * 1024
        return "handled", 404

    response = app.test_client().post(
        "/missing",
        data={"name": "upload", "file": (BytesIO(b"x" * 10 * 1024 * 1024), "file.bin")},
    )
    assert response.status_code == 404
    assert response.data == b"handled"
    response.close()


def test_routing_exception_traceback_is_preserved_after_response_closes(app):
    errors = []

    @app.errorhandler(404)
    def missing(error):
        errors.append(error)
        return "missing", 404

    response = app.test_client().post("/missing", json={"name": "value"})
    error = errors[0]
    traceback, context, cause = error.__traceback__, error.__context__, error.__cause__
    assert traceback is not None
    response.close()
    assert error.__traceback__ is traceback
    assert error.__context__ is context
    assert error.__cause__ is cause
