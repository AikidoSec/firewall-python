"""
Flask source module, intercepts flask import and adds Aikido middleware
"""

import copy
import importhook
from aikido_firewall.helpers.logging import logger
from aikido_firewall.context import Context
from aikido_firewall.background_process.packages import add_wrapped_package
from .functions.request_handler import request_handler
from aikido_firewall.context import get_current_context


def generate_aikido_view_func_wrapper(former_view_func):
    """
    Generates our own wrapper for the function in self.view_functions[]
    """

    def aikido_view_func(*args, **kwargs):
        from werkzeug.exceptions import HTTPException
        from flask.globals import request_ctx

        req = request_ctx.request
        # Set body :
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

            pre_response = request_handler(stage="pre_response")
        except Exception as e:
            logger.debug("Exception in aikido's view function : %s", e)
        if pre_response:
            return pre_response[0], pre_response[1]
        try:
            res = former_view_func(*args, **kwargs)
            status_code = 200
            if isinstance(res, tuple):
                status_code = res[1]
            elif hasattr(res, "status_code"):
                status_code = res.status_code
            request_handler(stage="post_response", status_code=status_code)
            return res
        except HTTPException as e:
            request_handler(stage="post_response", status_code=e.code)
            raise e

    return aikido_view_func


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
    Hook 'n wrap on `flask.app`
    Our goal is to wrap the __init__ function of the "Flask" class,
    so we can insert our middleware. Returns : Modified flask.app object

    Flask class |-> App class |-> Scaffold class
    @app.route is implemented in Scaffold and calls `add_url_rule` in App class
    This function writes to self.view_functions[endpoint] = view_func
    The only other reference where view_functions is called is on this line:
    https://github.com/pallets/flask/blob/8a6cdf1e2a5efa81c30f6166602064ceefb0a35b/src/flask/app.py#L882
    So we would have to wrap the `ensure_sync` function of the app object
    """
    modified_flask = importhook.copy_module(flask)

    def aikido_ensure_sync(_self, func):
        """
        We're wrapping this function, so we can wrap the passed along function `func`
        https://github.com/pallets/flask/blob/8a6cdf1e2a5efa81c30f6166602064ceefb0a35b/src/flask/app.py#L946
        """
        return generate_aikido_view_func_wrapper(func)

    setattr(modified_flask.Flask, "__call__", aikido___call__)
    setattr(modified_flask.Flask, "ensure_sync", aikido_ensure_sync)
    add_wrapped_package("flask")
    return modified_flask
