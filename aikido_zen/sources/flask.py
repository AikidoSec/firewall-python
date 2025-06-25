from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.helpers.logging import logger
from aikido_zen.context import Context
from aikido_zen.context import get_current_context
import aikido_zen.sources.functions.request_handler as funcs
from aikido_zen.sinks import (
    on_import,
    patch_function,
    after,
    before_modify_return,
    before,
)
from aikido_zen.sources.functions.request_handler import pre_response as should_block


@before_modify_return
def _full_dispatch_request_before(func, instance, args, kwargs):
    from flask.globals import request_ctx
    from flask import Response

    req = request_ctx.request
    extract_cookies_from_flask_request_and_save_data(req)
    extract_form_data_from_flask_request_and_save_data(req)
    extract_view_args_from_flask_request_and_save_data(req)

@after
def _full_dispatch_request_after(func, instance, args, kwargs, return_value):
    if not hasattr(return_value, "status_code"):
        return
    funcs.request_handler(stage="post_response", status_code=return_value.status_code)


def extract_view_args_from_flask_request_and_save_data(req):
    """Extract view args from flask request"""
    context = get_current_context()

    try:
        if getattr(req, "view_args"):
            context.route_params = dict(req.view_args)
            context.set_as_current_context()
    except Exception as e:
        logger.debug("Exception occurred whilst extracting flask view args data: %s", e)


def extract_form_data_from_flask_request_and_save_data(req):
    """Extract form data from flask request"""
    context = get_current_context()
    try:
        if context:
            if req.form:
                context.set_body(req.form)
            else:
                context.set_body(req.data.decode("utf-8"))
            context.set_as_current_context()
    except Exception as e:
        logger.debug("Exception occurred whilst extracting flask body data: %s", e)


def extract_cookies_from_flask_request_and_save_data(req):
    """Extract cookies from flask request"""
    context = get_current_context()
    try:
        context.cookies = req.cookies.to_dict()
        context.set_as_current_context()
    except Exception as e:
        logger.debug("Exception occurred whilst extracting flask cookie data: %s", e)


@before_modify_return
def _call(func, instance, args, kwargs):
    environ = get_argument(args, kwargs, 0, "environ")
    start_response = get_argument(args, kwargs, 1, "start_response")

    context1 = Context(req=environ, source="flask")
    context1.set_as_current_context()
    funcs.request_handler(stage="init")

    # Checks for blocked IPs, blocked UAs, ...
    should_block_current_request = should_block()
    if should_block_current_request is not None:
        from flask import Response
        msg, status_code = should_block_current_request
        return Response(msg, status=status_code, mimetype="text/plain")(environ, start_response)

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
