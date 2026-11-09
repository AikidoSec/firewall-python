from weakref import ref
from aikido_zen.context import Context
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import on_import, patch_function, before_modify_return, after
from .extract_cookies import extract_cookies_from_flask_request_and_save_data
from .extract_query import extract_query_from_flask_request_and_save_data
from .extract_view_args import extract_view_args_from_flask_request_and_save_data
import aikido_zen.sources.functions.request_handler as funcs
from aikido_zen.sources.functions.request_handler import pre_response as should_block


@before_modify_return
def _full_dispatch_request_before(func, instance, args, kwargs):
    from flask.globals import request_ctx

    req = request_ctx.request
    extract_cookies_from_flask_request_and_save_data(req)
    extract_view_args_from_flask_request_and_save_data(req)
    extract_query_from_flask_request_and_save_data(req)


@after
def _full_dispatch_request_after(func, instance, args, kwargs, return_value):
    if not hasattr(return_value, "status_code"):
        return
    funcs.request_handler(stage="post_response", status_code=return_value.status_code)


@after
def _body_read_after(func, instance, args, kwargs, return_value):
    context_ref = instance.environ.get("aikido_zen.context")
    context = context_ref() if context_ref is not None else None
    if context is None:
        return
    form = instance.__dict__.get("form")
    if form and context.body is not form:
        context.set_body(form)
        context.parsed_userinput.pop("body", None)
    elif context.body is None and return_value:
        context.set_body(return_value)


@before_modify_return
def _call(func, instance, args, kwargs):
    environ = get_argument(args, kwargs, 0, "environ")
    start_response = get_argument(args, kwargs, 1, "start_response")

    request_class = instance.request_class
    if not request_class.__dict__.get("_aikido_body_hooks_installed", False):
        patch_function(request_class, "get_data", _body_read_after)
        patch_function(request_class, "_load_form_data", _body_read_after)
        setattr(request_class, "_aikido_body_hooks_installed", True)

    context1 = Context(req=environ, source="flask")
    # Old requests may outlive their response; avoid retaining our captured data.
    environ["aikido_zen.context"] = ref(context1)
    context1.set_as_current_context()
    funcs.request_handler(stage="init")

    # Checks for blocked IPs, blocked UAs, ...
    should_block_current_request = should_block()
    if should_block_current_request is not None:
        from flask import Response

        msg, status_code = should_block_current_request
        try:
            return Response(msg, status=status_code, mimetype="text/plain")(
                environ, start_response
            )
        finally:
            # Match Flask's teardown because blocked requests never enter Flask.
            environ["werkzeug.request"] = None


@on_import("flask.app", "flask", version_requirement="2.2.4")
def patch(m):
    """
    patching module flask.appimport

    - patches: Flask.__call__, also done by Sentry.
    - patches: Flask.full_dispatch_request
    **Why?** full_dispatch_request gets called in the WSGI app. It gets called after all middleware. request_ctx is
    available, so we can extract data from it.
    (github src: https://github.com/pallets/flask/blob/bc143499cf1137a271a7cf75bdd3e16e43ede2f0/src/flask/app.py#L1529)
    """
    patch_function(m, "Flask.__call__", _call)
    patch_function(m, "Flask.full_dispatch_request", _full_dispatch_request_before)
    patch_function(m, "Flask.full_dispatch_request", _full_dispatch_request_after)
