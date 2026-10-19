from http import HTTPStatus

from aikido_zen.context import Context
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import (
    after,
    before,
    before_modify_return,
    on_import,
    patch_function,
)
import aikido_zen.sources.functions.request_handler as funcs
from aikido_zen.sources.functions.request_handler import pre_response as should_block

from .extract_request import save_parsed_request, save_route_args


def _plain_wsgi(start_response, message, status_code):
    if isinstance(message, str):
        body = message.encode()
    else:
        body = message or b""
    try:
        reason = HTTPStatus(status_code).phrase
    except ValueError:
        reason = "Error"
    start_response(
        f"{status_code} {reason}",
        [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]


@before_modify_return
def _call(func, instance, args, kwargs):
    environ = get_argument(args, kwargs, 0, "environ")
    start_response = get_argument(args, kwargs, 1, "start_response")

    context = Context(req=environ, source="odoo")
    context.set_as_current_context()
    funcs.request_handler(stage="init")

    blocked = should_block()
    if blocked is not None:
        message, status_code = blocked
        return _plain_wsgi(start_response, message, status_code)

    status_code = None

    def wrapped_start_response(status, response_headers, exc_info=None):
        nonlocal status_code
        try:
            status_code = int(str(status).split(" ", 1)[0])
        except (TypeError, ValueError):
            status_code = 0
        return start_response(status, response_headers, exc_info)

    result = func(environ, wrapped_start_response)
    if status_code is not None:
        funcs.request_handler(stage="post_response", status_code=status_code)
    return result


@before
def _dispatch(func, instance, args, kwargs):
    save_route_args(get_argument(args, kwargs, 1, "args"))


@after
def _get_json_data(func, instance, args, kwargs, return_value):
    # Odoo has already read wsgi.input, so store its parsed JSON. The controller
    # runs its SQL after this call.
    save_parsed_request(getattr(instance, "httprequest", None), body=return_value)


@after
def _get_http_params(func, instance, args, kwargs, return_value):
    save_parsed_request(getattr(instance, "httprequest", None), include_form=True)


@before
def _worker_http_start(func, instance, args, kwargs):
    # Prefork workers are forked after Odoo imports. protect() has to run in
    # the worker, as it does for gunicorn's post_fork.
    import aikido_zen

    aikido_zen.protect()


@on_import("odoo.http")
def patch(module):
    """
    Patch odoo.http once Odoo imports it. Distribution metadata is not
    required because Odoo is often a source checkout.
    """
    patch_function(module, "Application.__call__", _call)
    patch_function(module, "JsonRPCDispatcher.dispatch", _dispatch)
    patch_function(module, "HttpDispatcher.dispatch", _dispatch)
    patch_function(module, "Request.get_json_data", _get_json_data)
    patch_function(module, "Request.get_http_params", _get_http_params)


@on_import("odoo.service.server")
def patch_server(module):
    patch_function(module, "WorkerHTTP.start", _worker_http_start)
