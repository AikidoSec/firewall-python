"""
Flask source module, intercepts flask import and adds Aikido middleware
"""

import copy
import aikido_zen.importhook as importhook
from aikido_zen.helpers.logging import logger
from aikido_zen.context import Context
from aikido_zen.background_process.packages import is_package_compatible, ANY_VERSION
from aikido_zen.context import get_current_context
import aikido_zen.sources.functions.request_handler as funcs


def aik_full_dispatch_request(*args, former_full_dispatch_request=None, **kwargs):
    """
    Creates a new full_dispatch_request function :
    https://github.com/pallets/flask/blob/2fec0b206c6e83ea813ab26597e15c96fab08be7/src/flask/app.py#L884
    This function gets called in the wsgi_app. So this function onlygets called after all the
    middleware. This is important since we want to be able to access users. This also means the
    request in request_ctx is available and we can extract data from it This function also
    returns a response, so we can send status codes and error messages.
    """
    # pylint:disable=import-outside-toplevel # We don't want to install this by default
    try:
        from flask.globals import request_ctx
        from flask import Response
    except ImportError:
        logger.info("Flask not properly installed.")
        return former_full_dispatch_request(*args, **kwargs)

    req = request_ctx.request

    extract_cookies_from_flask_request_and_save_data(req)
    extract_form_data_from_flask_request_and_save_data(req)
    extract_view_args_from_flask_request_and_save_data(req)

    pre_response = funcs.request_handler(stage="pre_response")
    if pre_response:
        # This happens when a route is rate limited, a user blocked, etc...
        return Response(pre_response[0], status=pre_response[1], mimetype="text/plain")
    res = former_full_dispatch_request(*args, **kwargs)
    funcs.request_handler(stage="post_response", status_code=res.status_code)
    return res


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


def aikido___call__(flask_app, environ, start_response):
    """Aikido's __call__ wrapper"""
    # We don't want to install werkzeug :
    # pylint: disable=import-outside-toplevel
    try:
        context1 = Context(req=environ, source="flask")
        context1.set_as_current_context()
        funcs.request_handler(stage="init")
    except Exception as e:
        logger.debug("Exception on aikido __call__ function : %s", e)
    res = flask_app.wsgi_app(environ, start_response)
    return res


FLASK_REQUIRED_VERSION = "2.3.0"


@importhook.on_import("flask.app")
def on_flask_import(flask):
    """
    Hook 'n wrap on `flask.app`. Flask class |-> App class |-> Scaffold class
    @app.route |-> `add_url_rule` |-> self.view_functions. these get called via
    full_dispatch_request, which we wrap. We also wrap __call__ to run our middleware.
    """
    if not is_package_compatible("flask", required_version=FLASK_REQUIRED_VERSION):
        return flask
    modified_flask = importhook.copy_module(flask)
    former_fdr = copy.deepcopy(flask.Flask.full_dispatch_request)

    def aikido_wrapper_fdr(*args, **kwargs):
        return aik_full_dispatch_request(
            *args, former_full_dispatch_request=former_fdr, **kwargs
        )

    # pylint:disable=no-member # Pylint has issues with the wrapping
    setattr(modified_flask.Flask, "__call__", aikido___call__)
    setattr(modified_flask.Flask, "full_dispatch_request", aikido_wrapper_fdr)
    return modified_flask
