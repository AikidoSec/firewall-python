import contextvars
from weakref import ref

from aikido_zen.context import Context, current_context
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.helpers.logging import logger
from aikido_zen.sinks import after, before, on_import, patch_function
import aikido_zen.sources.functions.request_handler as funcs
from aikido_zen.sources.functions.request_handler import pre_response as should_block

from .extract_request import save_body, save_route_args, save_rpc_params

# Odoo's get_json_data reads the body with get_data. This flag stops Zen from storing
# that raw text and parsing it a second time.
_reading_json = contextvars.ContextVar("aikido_zen_odoo_reading_json", default=False)


def _call(func, instance, args, kwargs):
    environ = get_argument(args, kwargs, 0, "environ")
    start_response = get_argument(args, kwargs, 1, "start_response")

    try:
        context = Context(req=environ, source="odoo")
        environ["aikido_zen.context"] = ref(context)
        context.set_as_current_context()
        funcs.request_handler(stage="init")
        blocked = should_block()
    except Exception as e:
        logger.debug("Exception occurred in init stage (Odoo): %s", e)
        # Otherwise Odoo would run with the previous request's input as the context.
        current_context.set(None)
        return func(*args, **kwargs)

    if blocked is not None:
        from werkzeug.wrappers import Response

        message, status_code = blocked
        response = Response(message, status=status_code, mimetype="text/plain")
        return response(environ, start_response)

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
def _pre_dispatch(func, instance, args, kwargs):
    save_route_args(get_argument(args, kwargs, 1, "args"))


def _get_json_data(func, instance, args, kwargs):
    token = _reading_json.set(True)
    try:
        return_value = func(*args, **kwargs)
    finally:
        _reading_json.reset(token)
    save_body(getattr(instance, "httprequest", None), return_value)
    return return_value


@after
def _body_read(func, instance, args, kwargs, return_value):
    if not _reading_json.get():
        save_body(instance, return_value)


@before
def _worker_http_start(func, instance, args, kwargs):
    # Prefork workers are forked after Odoo imports. protect() has to run in
    # the worker, as it does for gunicorn's post_fork.
    import aikido_zen

    aikido_zen.protect()


@before
def _dispatch_rpc(func, instance, args, kwargs):
    # XML-RPC passes the values Odoo parsed from the body.
    save_rpc_params(get_argument(args, kwargs, 2, "params"))


HOOKS = {
    "Application.__call__": _call,
    # Inherited by every dispatcher, including Odoo 19's json2.
    "Dispatcher.pre_dispatch": _pre_dispatch,
    "Request.get_json_data": _get_json_data,
    # Odoo wraps werkzeug's Request, which reads the body in these two methods.
    "werkzeug.wrappers.Request.get_data": _body_read,
    "werkzeug.wrappers.Request._load_form_data": _body_read,
}


def _has_method(module, path):
    target = module
    for name in path.split("."):
        target = getattr(target, name, None)
    return callable(target)


def patch_odoo_http(module):
    missing = [path for path in HOOKS if not _has_method(module, path)]
    if missing:
        # Patching only some hooks would build a context without the body.
        logger.warning(
            "Odoo request protection disabled, odoo.http has no %s",
            ", ".join(missing),
        )
        return
    for path, wrapper in HOOKS.items():
        patch_function(module, path, wrapper)


# A post_load hook starts Zen after Odoo imported odoo.http. on_import then runs
# patch at once, so everything it calls must be defined above this line.
@on_import("odoo.http")
def patch(module):
    """
    Patch odoo.http once Odoo imports it. Distribution metadata is not
    required because Odoo is often a source checkout.
    """
    patch_odoo_http(module)


@on_import("odoo.service.server")
def patch_server(module):
    patch_function(module, "WorkerHTTP.start", _worker_http_start)


@on_import("odoo.addons.base.controllers.rpc")
def patch_rpc(module):
    patch_function(module, "dispatch_rpc", _dispatch_rpc)


@on_import("odoo.addons.rpc.controllers.xmlrpc")
def patch_xmlrpc(module):
    # Odoo 19 moved XML-RPC into its own addon.
    patch_function(module, "dispatch_rpc", _dispatch_rpc)
