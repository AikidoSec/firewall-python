import json
from types import SimpleNamespace
from unittest.mock import Mock, call, patch as mock_patch

import pytest
from werkzeug.exceptions import HTTPException
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request as WerkzeugRequest
from werkzeug.wrappers import Response

from aikido_zen.context import Context, current_context, get_current_context
from aikido_zen.errors import AikidoException
from aikido_zen.helpers.extract_strings_from_context import extract_strings_from_context
from aikido_zen.sinks import patch_function
from .lifecycle import patch


def make_environ(data=None, content_type=None, path="/items/7"):
    return EnvironBuilder(
        method="POST",
        path=path,
        query_string={"search": "value"},
        headers={"X-Test": "header", "Cookie": "session_id=secret"},
        data=data,
        content_type=content_type,
        base_url="https://example.com",
        environ_base={"REMOTE_ADDR": "198.51.100.23"},
    ).get_environ()


def make_http_module(version=16):
    class Request:
        init_calls = 0

        def __init__(self, httprequest):
            type(self).init_calls += 1
            self.httprequest = httprequest

        def get_json_data(self):
            return json.loads(self.httprequest.get_data(as_text=True))

        def make_response(self, data, headers=None, status=200):
            return Response(data, headers=headers, status=status)

    class Dispatcher:
        routing_type = "http"

        def __init__(self, request):
            self.request = request
            self.pre_calls = []
            self.post_calls = []
            self.pre_result = object()
            self.post_result = object()

        def pre_dispatch(self, rule, arguments):
            self.pre_calls.append((rule, arguments))
            return self.pre_result

        def post_dispatch(self, response):
            self.post_calls.append(response)
            return self.post_result

    class Application:
        def __init__(self, callback=lambda _environ, _start_response: []):
            self.callback = callback

        def __call__(self, environ, start_response):
            return self.callback(environ, start_response)

    return SimpleNamespace(
        Request=Request,
        Dispatcher=Dispatcher,
        Application=Application,
        odoo=SimpleNamespace(
            release=SimpleNamespace(version_info=(version, 0, 0, "final", 0, ""))
        ),
    )


def make_rule(route="/items/<int:item_id>/"):
    return SimpleNamespace(rule=route)


@pytest.fixture(autouse=True)
def reset_context():
    current_context.set(None)
    yield
    current_context.set(None)


@pytest.mark.parametrize("version", [15, 20, None])
def test_patch_fails_open_for_unsupported_or_malformed_versions(version, caplog):
    module = make_http_module(16)
    module.odoo.release.version_info = None if version is None else (version, 0)

    patch(module)
    module.Request(WerkzeugRequest(make_environ()))

    assert get_current_context() is None
    assert "Odoo request protection disabled" in caplog.text


def test_patch_fails_open_when_a_required_lifecycle_hook_is_missing(caplog):
    module = make_http_module()
    del module.Dispatcher.post_dispatch

    patch(module)
    module.Request(WerkzeugRequest(make_environ()))

    assert get_current_context() is None
    assert "Odoo request protection disabled" in caplog.text


@pytest.mark.parametrize("version", [16, 17, 18, 19])
def test_request_initialization_sets_wsgi_context_after_odoo_initialization(version):
    module = make_http_module(version)

    with mock_patch("aikido_zen.sources.odoo.lifecycle.request_handler") as handler:
        patch(module)
        request = module.Request(WerkzeugRequest(make_environ()))

    context = get_current_context()
    assert request.httprequest.method == "POST"
    assert context.source == "odoo"
    assert context.method == "POST"
    assert context.url == "https://example.com/items/7"
    assert context.query == {"search": ["value"]}
    assert context.headers.get_header("X_TEST") == "header"
    assert context.cookies == {"session_id": "secret"}
    assert context.remote_address == "198.51.100.23"
    handler.assert_called_once_with(stage="init")


def test_pre_dispatch_enriches_context_without_mutating_odoo_arguments():
    module = make_http_module()
    environ = make_environ(
        data={"tag": ["first", "second"]},
        content_type="application/x-www-form-urlencoded",
    )

    with mock_patch(
        "aikido_zen.sources.odoo.lifecycle.request_handler", return_value=None
    ) as handler:
        patch(module)
        request = module.Request(WerkzeugRequest(environ))
        dispatcher = module.Dispatcher(request)
        rule = make_rule()
        arguments = {"item_id": 7, "slug": "actual-route", "record": object()}
        original_arguments = arguments.copy()
        get_current_context().parsed_userinput = {
            "body": {"stale-body": ""},
            "route_params": {"stale-route": ""},
        }

        result = dispatcher.pre_dispatch(rule, arguments)

    context = get_current_context()
    assert result is dispatcher.pre_result
    assert dispatcher.pre_calls == [(rule, arguments)]
    assert arguments == original_arguments
    assert context.route == "/items/:number"
    assert context.route_params == {"item_id": 7, "slug": "actual-route"}
    assert context.body == {"tag": ["first", "second"]}
    assert context.user is None
    extracted_values = {
        value for value, _path, _source in extract_strings_from_context(context)
    }
    assert "actual-route" in extracted_values
    assert "first" in extracted_values
    assert "stale-body" not in extracted_values
    assert "stale-route" not in extracted_values
    assert handler.call_args_list == [call(stage="init"), call(stage="pre_response")]


def test_pre_dispatch_enrichment_runs_at_most_once():
    module = make_http_module()

    with mock_patch(
        "aikido_zen.sources.odoo.lifecycle.extract_body"
    ) as extract_request_body, mock_patch(
        "aikido_zen.sources.odoo.lifecycle.request_handler", return_value=None
    ) as handler:
        patch(module)
        request = module.Request(WerkzeugRequest(make_environ()))
        dispatcher = module.Dispatcher(request)
        rule = make_rule()

        dispatcher.pre_dispatch(rule, {})
        dispatcher.pre_dispatch(rule, {})

    assert dispatcher.pre_calls == [(rule, {}), (rule, {})]
    extract_request_body.assert_called_once_with(request, "http")
    assert handler.call_args_list == [call(stage="init"), call(stage="pre_response")]


def test_pre_dispatch_aborts_before_controller_for_request_policy_blocks():
    module = make_http_module()

    def handle_request(stage, status_code=0):
        if stage == "pre_response":
            return "Your IP address is blocked.", 403
        return None

    with mock_patch(
        "aikido_zen.sources.odoo.lifecycle.request_handler",
        side_effect=handle_request,
    ):
        patch(module)
        request = module.Request(WerkzeugRequest(make_environ()))
        dispatcher = module.Dispatcher(request)

        with pytest.raises(HTTPException) as raised:
            dispatcher.pre_dispatch(make_rule(), {})

    response = raised.value.get_response()
    assert dispatcher.pre_calls == [(dispatcher.pre_calls[0][0], {})]
    assert response.status_code == 403
    assert response.get_data(as_text=True) == "Your IP address is blocked."


def test_request_policy_abort_failure_does_not_break_the_odoo_request():
    module = make_http_module()

    with mock_patch(
        "aikido_zen.sources.odoo.lifecycle.request_handler",
        side_effect=lambda stage, status_code=0: (
            ("Blocked", 403) if stage == "pre_response" else None
        ),
    ), mock_patch(
        "werkzeug.exceptions.abort", side_effect=RuntimeError("abort failed")
    ):
        patch(module)
        request = module.Request(WerkzeugRequest(make_environ()))
        dispatcher = module.Dispatcher(request)

        result = dispatcher.pre_dispatch(make_rule(), {})

    assert result is dispatcher.pre_result
    assert len(dispatcher.pre_calls) == 1


def test_pre_dispatch_failure_does_not_break_the_odoo_request(caplog):
    module = make_http_module()

    with mock_patch(
        "aikido_zen.sources.odoo.lifecycle.request_handler", return_value=None
    ), mock_patch(
        "aikido_zen.sources.odoo.lifecycle.extract_body",
        side_effect=ValueError("malformed body containing a secret"),
    ):
        patch(module)
        request = module.Request(WerkzeugRequest(make_environ()))
        dispatcher = module.Dispatcher(request)

        result = dispatcher.pre_dispatch(make_rule(), {})

    assert result is dispatcher.pre_result
    assert len(dispatcher.pre_calls) == 1
    assert "malformed body containing a secret" not in caplog.text


def test_post_dispatch_records_a_response_at_most_once():
    module = make_http_module()

    with mock_patch("aikido_zen.sources.odoo.lifecycle.request_handler") as handler:
        patch(module)
        request = module.Request(WerkzeugRequest(make_environ()))
        dispatcher = module.Dispatcher(request)
        response = Response(status=201)
        handler.reset_mock()

        first_result = dispatcher.post_dispatch(response)
        second_result = dispatcher.post_dispatch(response)

    assert first_result is dispatcher.post_result
    assert second_result is dispatcher.post_result
    assert dispatcher.post_calls == [response, response]
    handler.assert_called_once_with(stage="post_response", status_code=201)


@pytest.mark.parametrize(
    ("path", "status"),
    [
        ("/web/static/src/img/logo.png", "200 OK"),
        ("/.env", "404 Not Found"),
    ],
)
def test_application_records_responses_that_bypass_dispatcher(path, status):
    module = make_http_module()

    def application(environ, start_response):
        module.Request(WerkzeugRequest(environ))
        start_response(status, [])
        return []

    with mock_patch("aikido_zen.sources.odoo.lifecycle.request_handler") as handler:
        patch(module)
        response = module.Application(application)(
            make_environ(path=path),
            Mock(),
        )

    assert list(response) == []
    handler.assert_has_calls(
        [
            call(stage="init"),
            call(stage="post_response", status_code=int(status[:3])),
        ]
    )


def test_application_restores_context_and_reactivates_it_while_streaming():
    module = make_http_module()
    previous_context = Context()
    request_context = Context()
    request_context.source = "odoo"
    chunk = b"response chunk"
    iterator_error = RuntimeError("stream failed")

    class Stream:
        def __init__(self):
            self.iterated_in = None
            self.next_contexts = []
            self.closed_in = None
            self.next_calls = 0

        def __iter__(self):
            self.iterated_in = get_current_context()
            return self

        def __next__(self):
            self.next_contexts.append(get_current_context())
            self.next_calls += 1
            if self.next_calls == 1:
                return chunk
            raise iterator_error

        def close(self):
            self.closed_in = get_current_context()
            return "closed"

    stream = Stream()

    def application(_environ, _start_response):
        request_context.set_as_current_context()
        return stream

    current_context.set(previous_context)
    patch(module)
    result = module.Application(application)(make_environ(), Mock())

    assert get_current_context() is previous_context
    assert next(result) is chunk
    assert get_current_context() is previous_context
    with pytest.raises(RuntimeError) as raised:
        next(result)
    assert raised.value is iterator_error
    assert get_current_context() is previous_context
    assert result.close() == "closed"
    assert stream.iterated_in is request_context
    assert stream.next_contexts == [request_context, request_context]
    assert stream.closed_in is request_context
    assert get_current_context() is previous_context


def test_application_restores_context_when_odoo_raises():
    module = make_http_module()
    previous_context = Context()
    request_context = Context()
    request_context.source = "odoo"
    application_error = AikidoException("blocked")

    def application(_environ, _start_response):
        request_context.set_as_current_context()
        raise application_error

    current_context.set(previous_context)
    patch(module)

    with pytest.raises(AikidoException) as raised:
        module.Application(application)(make_environ(), Mock())

    assert raised.value is application_error
    assert get_current_context() is previous_context


@pytest.mark.parametrize("zen_first", [True, False])
def test_patch_coexists_with_another_wrapper(zen_first):
    module = make_http_module()
    observed_calls = []

    def observer(wrapped, instance, args, kwargs):
        observed_calls.append((args, kwargs))
        return wrapped(*args, **kwargs)

    if zen_first:
        patch(module)
        patch_function(module, "Dispatcher.pre_dispatch", observer)
    else:
        patch_function(module, "Dispatcher.pre_dispatch", observer)
        patch(module)

    with mock_patch(
        "aikido_zen.sources.odoo.lifecycle.request_handler", return_value=None
    ):
        request = module.Request(WerkzeugRequest(make_environ()))
        dispatcher = module.Dispatcher(request)
        dispatcher.pre_dispatch(make_rule(), {})

    assert len(observed_calls) == 1
    assert len(dispatcher.pre_calls) == 1


def test_repeated_patch_does_not_duplicate_lifecycle_handlers():
    module = make_http_module()

    with mock_patch("aikido_zen.sources.odoo.lifecycle.request_handler") as handler:
        patch(module)
        patch(module)
        module.Request(WerkzeugRequest(make_environ()))

    handler.assert_called_once_with(stage="init")
