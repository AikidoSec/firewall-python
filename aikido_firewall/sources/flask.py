"""
Flask source module, intercepts flask import and adds Aikido middleware
"""

import copy
import importhook
from aikido_firewall.helpers.logging import logger
from aikido_firewall.context import Context
from aikido_firewall.background_process.packages import add_wrapped_package
from aikido_firewall.context import get_current_context
from .functions.request_handler import request_handler


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
    extract_and_save_data_from_flask_request(req)
    pre_response = request_handler(stage="pre_response")
    if pre_response:
        return Response(pre_response[0], status=pre_response[1], mimetype="text/plain")
    res = former_full_dispatch_request(*args, **kwargs)
    request_handler(stage="post_response", status_code=res.status_code)
    return res


def extract_and_save_data_from_flask_request(req):
    """Extract form, json, data, ... from flask request"""
    try:
        context = get_current_context()
        if context:
            if req.is_json:
                context.body = req.get_json()
            elif req.form:
                context.body = req.form
            else:
                context.body = req.data.decode("utf-8")
            context.cookies = req.cookies.to_dict()
            context.set_as_current_context()
    except Exception as e:
        logger.debug("Exception occured whilst extracting flask body data: %s", e)


def aikido___call__(flask_app, environ, start_response):
    """Aikido's __call__ wrapper"""
    # We don't want to install werkzeug :
    # pylint: disable=import-outside-toplevel
    try:
        context1 = Context(req=environ, source="flask")
        context1.set_as_current_context()
        request_handler(stage="init")
    except Exception as e:
        logger.debug("Exception on aikido __call__ function : %s", e)
    res = flask_app.wsgi_app(environ, start_response)
    return res


@importhook.on_import("flask.app")
def on_flask_import(flask):
    """
    Hook 'n wrap on `flask.app`. Flask class |-> App class |-> Scaffold class
    @app.route |-> `add_url_rule` |-> self.view_functions. these get called via
    full_dispatch_request, which we wrap. We also wrap __call__ to run our middleware.
    """
    modified_flask = importhook.copy_module(flask)
    former_fdr = copy.deepcopy(flask.Flask.full_dispatch_request)

    def aikido_wrapper_fdr(*args, **kwargs):
        return aik_full_dispatch_request(
            *args, former_full_dispatch_request=former_fdr, **kwargs
        )

    # pylint:disable=no-member # Pylint has issues with the wrapping
    setattr(modified_flask.Flask, "__call__", aikido___call__)
    setattr(modified_flask.Flask, "full_dispatch_request", aikido_wrapper_fdr)
    add_wrapped_package("flask")
    return modified_flask
