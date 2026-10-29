import gc
import json
from io import BytesIO
from weakref import ref

import pytest
from flask import Flask, Response, copy_current_request_context, request, send_file
from werkzeug.datastructures import MultiDict

import aikido_zen.sources.flask as source
from aikido_zen.api_discovery.get_api_info import get_api_info
from aikido_zen.context import current_context, get_current_context
from aikido_zen.vulnerabilities.nosql_injection import detect_nosql_injection
from aikido_zen.vulnerabilities.sql_injection.context_contains_sql_injection import (
    context_contains_sql_injection,
)


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


@pytest.mark.parametrize("status", [404, 405, 308])
@pytest.mark.parametrize("hooks", [False, True])
def test_unread_error_body_is_not_captured(app, status, hooks):
    app.add_url_rule("/known", view_func=lambda: "ok")
    app.add_url_rule(
        "/redirect/", endpoint="redirect", view_func=lambda: "ok", methods=["POST"]
    )
    if hooks:
        app.before_request(lambda: None)
        app.after_request(lambda response: response)
        app.register_error_handler(404, lambda error: ("missing", 404))
    stream = CountingInput(b"x" * 24 * 1024 * 1024)
    path = {404: "/missing", 405: "/known", 308: "/redirect"}[status]
    response = app.test_client().post(
        path, input_stream=stream, content_type="application/octet-stream"
    )
    assert response.status_code == status
    assert stream.reads == 0
    assert get_current_context().__dict__["body"] is None
    response.close()


@pytest.mark.parametrize(
    "reader",
    [
        "data",
        "get_data",
        "get_data_text",
        "get_data_no_cache",
        "json",
        "get_json",
        "get_json_force",
    ],
)
def test_json_capture_before_body_reader_returns(app, reader):
    @app.post("/body")
    def view():
        if reader == "data":
            data = request.data
        elif reader == "get_data_text":
            data = request.get_data(as_text=True)
        elif reader == "get_data_no_cache":
            data = request.get_data(cache=False)
        elif reader == "json":
            data = request.json
        elif reader == "get_json_force":
            data = request.get_json(force=True)
        else:
            data = getattr(request, reader)()
        assert data
        assert get_current_context().body == {"name": "value"}
        return "ok"

    content_type = "text/plain" if reader == "get_json_force" else "application/json"
    response = app.test_client().post(
        "/body", data=b'{"name":"value"}', content_type=content_type
    )
    assert response.status_code == 200
    response.close()


@pytest.mark.parametrize(
    "reader",
    [
        "read",
        "readline",
        "readlines",
        "readinto",
        "iter",
        "next",
        "input_stream",
        "wsgi_input",
    ],
)
def test_raw_stream_reads_keep_body_available_for_inspection(app, reader):
    @app.post("/body")
    def view():
        if reader == "wsgi_input":
            request.environ["wsgi.input"].read()
        elif reader == "input_stream":
            request.input_stream.read()
        elif reader == "readinto":
            request.stream.readinto(bytearray(3))
        elif reader == "iter":
            list(request.stream)
        elif reader == "next":
            next(request.stream, None)
        else:
            getattr(request.stream, reader)()
        assert get_current_context().body == {"name": "value"}
        return "ok"

    response = app.test_client().post(
        "/body", data=b'{"name":"value"}', content_type="application/json"
    )
    assert response.status_code == 200
    response.close()


def test_inspection_can_load_body_without_application_read(app):
    attack = "Malicious Pet', 'Gru from the Minions') --"

    @app.post("/body")
    def view():
        result = context_contains_sql_injection(
            sql=f"INSERT INTO pets(name) VALUES ('{attack}')",
            operation="psycopg2.Cursor.execute",
            context=get_current_context(),
            dialect="postgres",
        )
        assert result["source"] == "body"
        assert result["payload"] == attack
        return "ok"

    response = app.test_client().post("/body", json={"name": attack})
    assert response.status_code == 200
    response.close()


def test_nosql_inspection_can_load_body_without_application_read(app):
    @app.post("/body")
    def view():
        result = detect_nosql_injection(get_current_context(), {"title": {"$ne": None}})
        assert result["source"] == "body"
        assert result["injection"]
        return "ok"

    response = app.test_client().post("/body", json={"title": {"$ne": None}})
    assert response.status_code == 200
    response.close()


def test_schema_discovery_can_load_unused_body(app, monkeypatch):
    schemas = []

    def discover(stage, status_code=0):
        if stage == "post_response":
            schemas.append(get_api_info(get_current_context()))

    monkeypatch.setattr(source.funcs, "request_handler", discover)
    app.add_url_rule("/body", methods=["POST"], view_func=lambda: "ok")
    response = app.test_client().post("/body", json={"name": "value"})
    assert response.status_code == 200
    assert schemas[0]["body"] == {
        "type": "json",
        "schema": {"type": "object", "properties": {"name": {"type": "string"}}},
    }
    response.close()


def test_form_fields_and_duplicates_are_preserved(app):
    @app.post("/body")
    def view():
        assert request.form.getlist("name") == ["first", "second"]
        assert get_current_context().body.getlist("name") == ["first", "second"]
        return "ok"

    response = app.test_client().post(
        "/body", data=MultiDict([("name", "first"), ("name", "second")])
    )
    assert response.status_code == 200
    response.close()


def test_large_file_is_available_and_not_added_to_inspected_form(app):
    @app.post("/body")
    def view():
        assert len(request.files["file"].read()) == 10 * 1024 * 1024
        assert get_current_context().body.getlist("name") == ["upload"]
        assert "file" not in get_current_context().body
        assert request.form["name"] == "upload"
        return "ok"

    response = app.test_client().post(
        "/body",
        data={
            "name": "upload",
            "file": (BytesIO(b"x" * 10 * 1024 * 1024), "large.bin"),
        },
    )
    assert response.status_code == 200
    response.close()


def test_large_json_remains_supported(app):
    @app.post("/body")
    def view():
        data = request.get_json()
        assert len(data["padding"]) == 10 * 1024 * 1024
        assert get_current_context().body == data
        return "ok"

    response = app.test_client().post("/body", json={"padding": "x" * 10 * 1024 * 1024})
    assert response.status_code == 200
    response.close()


def test_chunked_body_without_content_length_is_captured(app):
    @app.post("/body")
    def view():
        assert request.get_json() == {"name": "value"}
        assert get_current_context().body == {"name": "value"}
        return "ok"

    response = app.test_client().post(
        "/body",
        data=b'{"name":"value"}',
        content_type="application/json",
        environ_overrides={"CONTENT_LENGTH": "", "wsgi.input_terminated": True},
    )
    assert response.status_code == 200
    response.close()


def test_application_json_mutations_do_not_change_captured_input(app):
    @app.post("/body")
    def view():
        request.get_json()["name"] = "changed"
        assert get_current_context().body == {"name": "original"}
        return "ok"

    response = app.test_client().post("/body", json={"name": "original"})
    assert response.status_code == 200
    response.close()


def test_direct_passthrough_response_keeps_body_available(app):
    @app.post("/body")
    def view():
        def generate():
            gc.collect()
            yield json.dumps(get_current_context().body).encode()

        return Response(generate(), direct_passthrough=True)

    response = app.test_client().post("/body", json={"name": "value"}, buffered=True)
    assert response.status_code == 200
    assert json.loads(response.data) == {"name": "value"}
    response.close()


def test_file_error_leaves_unused_body_unread(app, tmp_path):
    path = tmp_path / "missing.txt"
    path.write_bytes(b"missing")

    @app.errorhandler(404)
    def missing(error):
        return send_file(path), 404

    stream = CountingInput(b"x" * 1024 * 1024)
    response = app.test_client().post("/missing", input_stream=stream)
    assert response.status_code == 404
    assert response.data == b"missing"
    response.close()
    assert stream.reads == 0


def test_routing_exception_traceback_is_preserved_after_response_close(app):
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


@pytest.mark.parametrize("inspect_first", [False, True])
@pytest.mark.parametrize("intervening_request", [False, True])
@pytest.mark.parametrize("encoding", ["json", "form", "multipart"])
def test_copied_request_context_can_capture_body_after_response_closes(
    app, inspect_first, intervening_request, encoding
):
    callbacks = []
    uploads = []
    attack = "Malicious Pet', 'Gru from the Minions') --"
    app.add_url_rule("/other", view_func=lambda: "ok", methods=["POST"])

    @app.errorhandler(404)
    def missing(error):
        context = get_current_context()

        @copy_current_request_context
        def later():
            if inspect_first:
                result = context_contains_sql_injection(
                    sql=f"INSERT INTO pets(name) VALUES ('{attack}')",
                    operation="psycopg2.Cursor.execute",
                    context=context,
                    dialect="postgres",
                )
                assert result["source"] == "body"
            if encoding == "json":
                assert request.get_json() == {"name": attack}
            else:
                assert request.form["name"] == attack
            assert context.body["name"] == attack
            if encoding == "multipart":
                assert request.files["file"].read() == b"upload"
                uploads.append(request.files["file"].stream)

        callbacks.append(later)
        return "missing", 404

    client = app.test_client()
    if encoding == "json":
        response = client.post("/missing", json={"name": attack})
    else:
        data = {"name": attack}
        if encoding == "multipart":
            data["file"] = (BytesIO(b"upload"), "file.txt")
        response = client.post("/missing", data=data)
    assert response.status_code == 404
    response.close()
    assert get_current_context().__dict__["body"] is None
    if intervening_request:
        other = client.post("/other", json={"other": "request"})
        other.close()
    callbacks.pop()()
    if intervening_request:
        assert get_current_context().__dict__["body"] is None
    assert all(upload.closed for upload in uploads)


def test_body_can_be_captured_by_application_response_close_callback(app):
    captured = []

    @app.post("/body")
    def view():
        req = request._get_current_object()
        context = get_current_context()
        response = Response("ok")

        def on_close():
            captured.append((req.get_json(), context.body))

        response.call_on_close(on_close)
        return response

    response = app.test_client().post("/body", json={"name": "value"})
    response.close()
    assert captured == [({"name": "value"}, {"name": "value"})]


def test_streamed_response_can_inspect_body_after_request_teardown(app):
    @app.post("/body")
    def view():
        def generate():
            gc.collect()
            yield json.dumps(get_current_context().body)

        return generate()

    response = app.test_client().post("/body", json={"name": "value"}, buffered=True)
    assert response.status_code == 200
    assert json.loads(response.data) == {"name": "value"}
    response.close()


def test_uploads_opened_during_response_streaming_are_closed(app):
    streams = []

    @app.post("/body")
    def view():
        req = request._get_current_object()

        def generate():
            assert get_current_context().body.getlist("name") == ["upload"]
            streams.append(req.files["file"].stream)
            yield b"ok"

        return generate()

    response = app.test_client().post(
        "/body",
        data={"name": "upload", "file": (BytesIO(b"file"), "file.bin")},
        buffered=True,
    )
    assert response.status_code == 200
    response.close()
    assert streams[0].closed


def test_unread_request_is_not_retained_by_body_loader(app):
    requests = []

    @app.before_request
    def remember():
        requests.append(ref(request._get_current_object()))

    response = app.test_client().post("/missing", data=b"body")
    response.close()
    del response
    gc.collect()
    assert requests[0]() is None
    assert get_current_context().__dict__["body"] is None


@pytest.mark.parametrize(
    "data,status", [(b'{"invalid":', 400), (b'{"name":"\xff"}', 400)]
)
def test_invalid_json_errors_are_preserved(app, data, status):
    @app.post("/body")
    def view():
        request.get_json()
        return "ok"

    response = app.test_client().post(
        "/body", data=data, content_type="application/json"
    )
    assert response.status_code == status
    response.close()


def test_application_body_limit_is_preserved(app):
    app.config["MAX_CONTENT_LENGTH"] = 8

    @app.post("/body")
    def view():
        assert get_current_context().query == {"search": ["value"]}
        request.get_data()
        return "ok"

    response = app.test_client().post("/body?search=value", data=b"x" * 32)
    assert response.status_code == 413
    response.close()
