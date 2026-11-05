import pytest
import signal
from unittest.mock import patch
import aikido_zen.sources.flask
from aikido_zen.background_process.ipc import IPCClient
from aikido_zen.context import current_context, get_current_context

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


@pytest.mark.parametrize("inspect_raw_first", [False, True])
def test_form_body_after_raw_read_is_inspected(monkeypatch, inspect_raw_first):
    from flask import Flask, request
    from aikido_zen.helpers.extract_strings_from_context import (
        extract_strings_from_context,
    )
    from aikido_zen.vulnerabilities.sql_injection.context_contains_sql_injection import (
        context_contains_sql_injection,
    )

    monkeypatch.setattr(aikido_zen.sources.flask, "should_block", lambda: None)
    monkeypatch.setattr(
        aikido_zen.sources.flask.funcs, "request_handler", lambda **kwargs: None
    )
    app = Flask(__name__)
    attack = "Malicious Pet', 'Gru from the Minions') --"

    @app.post("/body")
    def view():
        request.get_data()
        context = get_current_context()
        if inspect_raw_first:
            extract_strings_from_context(context)
        name = request.form["name"]
        result = context_contains_sql_injection(
            sql=f"INSERT INTO pets(name) VALUES ('{name}')",
            operation="psycopg2.Cursor.execute",
            context=context,
            dialect="postgres",
        )
        assert result["source"] == "body"
        assert result["payload"] == attack
        return "ok"

    try:
        response = app.test_client().post("/body", data={"name": attack})
        assert response.status_code == 200
        response.close()
    finally:
        current_context.set(None)


@pytest.fixture
def body_app(monkeypatch):
    from flask import Flask

    monkeypatch.setattr(aikido_zen.sources.flask, "should_block", lambda: None)
    monkeypatch.setattr(
        aikido_zen.sources.flask.funcs, "request_handler", lambda **kwargs: None
    )
    current_context.set(None)
    yield Flask(__name__)
    current_context.set(None)


@pytest.mark.parametrize("status", [200, 404, 405, 308])
@pytest.mark.parametrize("hooks", [False, True])
def test_unused_body_is_not_read(body_app, status, hooks):
    from io import BytesIO

    body_app.add_url_rule("/known", endpoint="known", view_func=lambda: "ok")
    body_app.add_url_rule(
        "/ignored", endpoint="ignored", view_func=lambda: "ok", methods=["POST"]
    )
    body_app.add_url_rule(
        "/redirect/", endpoint="redirect", view_func=lambda: "ok", methods=["POST"]
    )
    if hooks:
        body_app.before_request(lambda: None)
        body_app.after_request(lambda response: response)
        body_app.register_error_handler(404, lambda error: ("missing", 404))
    stream = BytesIO(b"x" * 1024 * 1024)
    path = {200: "/ignored", 404: "/missing", 405: "/known", 308: "/redirect"}[status]
    with patch.object(stream, "read", wraps=stream.read) as read, patch.object(
        stream, "readinto", wraps=stream.readinto
    ) as readinto:
        response = body_app.test_client().post(path, input_stream=stream)
        assert response.status_code == status
        read.assert_not_called()
        readinto.assert_not_called()
        assert get_current_context().body is None
        response.close()


@pytest.mark.parametrize(
    "reader",
    [
        "stream",
        "chunks",
        "input_stream",
        "wsgi_input",
        "data",
        "get_data",
        "get_data_text",
        "get_data_no_cache",
        "get_json",
        "json",
    ],
)
def test_body_readers_preserve_application_data(body_app, reader):
    import json
    from flask import request

    data = {"name": "original"}
    payload = json.dumps(data).encode()

    @body_app.post("/body")
    def view():
        if reader == "stream":
            result = request.stream.read()
        elif reader == "chunks":
            result = request.stream.read(3) + request.stream.read()
        elif reader == "input_stream":
            result = request.input_stream.read()
        elif reader == "wsgi_input":
            result = request.environ["wsgi.input"].read()
        elif reader == "get_data_text":
            result = request.get_data(as_text=True)
        elif reader == "get_data_no_cache":
            result = request.get_data(cache=False)
        elif reader in ("data", "json"):
            result = getattr(request, reader)
        else:
            result = getattr(request, reader)()
        if reader in ("get_json", "json"):
            assert result == data
        elif reader == "get_data_text":
            assert result == payload.decode()
        else:
            assert result == payload
        assert get_current_context().body == data
        return "ok"

    response = body_app.test_client().post(
        "/body", data=payload, content_type="application/json"
    )
    assert response.status_code == 200
    response.close()


def test_large_upload_remains_available_and_only_form_fields_are_captured(body_app):
    from io import BytesIO
    from flask import request

    @body_app.post("/body")
    def view():
        assert len(request.files["file"].read()) == 10 * 1024 * 1024
        assert get_current_context().body.getlist("name") == ["upload"]
        assert "file" not in get_current_context().body
        return "ok"

    response = body_app.test_client().post(
        "/body",
        data={"name": "upload", "file": (BytesIO(b"x" * 10 * 1024 * 1024), "x.bin")},
    )
    assert response.status_code == 200
    response.close()


@pytest.mark.parametrize("reader", ["json", "form", "data"])
def test_body_read_during_session_setup_is_inspected(body_app, reader):
    import json
    from flask import session
    from flask.sessions import SecureCookieSession, SecureCookieSessionInterface
    from aikido_zen.vulnerabilities.sql_injection.context_contains_sql_injection import (
        context_contains_sql_injection,
    )

    attack = "Malicious Pet', 'Gru from the Minions') --"

    class BodySession(SecureCookieSessionInterface):
        def open_session(self, app, req):
            if reader == "json":
                data = req.get_json()
            elif reader == "form":
                data = req.form
            else:
                data = json.loads(req.get_data())
            return SecureCookieSession({"name": data["name"]})

    body_app.secret_key = "test-key"
    body_app.session_interface = BodySession()

    @body_app.post("/body")
    def view():
        name = session["name"]
        result = context_contains_sql_injection(
            sql=f"INSERT INTO pets(name) VALUES ('{name}')",
            operation="psycopg2.Cursor.execute",
            context=get_current_context(),
            dialect="postgres",
        )
        assert result["source"] == "body"
        assert result["payload"] == attack
        return "ok"

    data = (
        {"data": {"name": attack}} if reader == "form" else {"json": {"name": attack}}
    )
    response = body_app.test_client().post("/body", **data)
    assert response.status_code == 200
    response.close()


@pytest.mark.parametrize("reader", ["json", "data", "get_data"])
def test_custom_request_body_reader_is_inspected(body_app, reader):
    import json
    from flask import Request, request
    from werkzeug.wrappers import Request as WerkzeugRequest
    from aikido_zen.vulnerabilities.sql_injection.context_contains_sql_injection import (
        context_contains_sql_injection,
    )

    attack = "Malicious Pet', 'Gru from the Minions') --"

    class CustomRequest(Request):
        def get_data(self, *args, **kwargs):
            return WerkzeugRequest.get_data(self, *args, **kwargs)

    @body_app.post("/body")
    def view():
        if reader == "json":
            name = request.get_json()["name"]
        else:
            data = request.data if reader == "data" else request.get_data()
            name = json.loads(data)["name"]
        result = context_contains_sql_injection(
            sql=f"INSERT INTO pets(name) VALUES ('{name}')",
            operation="psycopg2.Cursor.execute",
            context=get_current_context(),
            dialect="postgres",
        )
        assert result["source"] == "body"
        assert result["payload"] == attack
        return "ok"

    client = body_app.test_client()
    response = client.post("/body", json={"name": attack})
    assert response.status_code == 200
    response.close()
    body_app.request_class = CustomRequest
    response = client.post("/body", json={"name": attack})
    assert response.status_code == 200
    response.close()
    wrapped = CustomRequest.__dict__["get_data"]
    response = client.post("/body", json={"name": attack})
    assert response.status_code == 200
    response.close()
    assert CustomRequest.__dict__["get_data"] is wrapped


@pytest.mark.parametrize(
    "reader", ["stream", "chunks", "lines", "input_stream", "wsgi_input"]
)
def test_body_read_from_raw_stream_is_inspected(body_app, reader):
    import json
    from flask import request
    from aikido_zen.vulnerabilities.sql_injection.context_contains_sql_injection import (
        context_contains_sql_injection,
    )

    attack = "Malicious Pet', 'Gru from the Minions') --"

    @body_app.post("/body")
    def view():
        if reader == "stream":
            raw = request.stream.read()
        elif reader == "chunks":
            raw = request.stream.read(3) + request.stream.read()
        elif reader == "lines":
            raw = b"".join(request.stream)
        elif reader == "input_stream":
            raw = request.input_stream.read()
        else:
            raw = request.environ["wsgi.input"].read()
        name = json.loads(raw)["name"]
        result = context_contains_sql_injection(
            sql=f"INSERT INTO pets(name) VALUES ('{name}')",
            operation="psycopg2.Cursor.execute",
            context=get_current_context(),
            dialect="postgres",
        )
        assert result["source"] == "body"
        assert result["payload"] == attack
        return "ok"

    response = body_app.test_client().post("/body", json={"name": attack})
    assert response.status_code == 200
    response.close()
