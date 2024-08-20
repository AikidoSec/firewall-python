"""
Flask source module, intercepts flask import and adds Aikido middleware
"""

import copy
import json
from io import BytesIO
import importhook
from aikido_firewall.helpers.logging import logger
from aikido_firewall.context import Context
from aikido_firewall.background_process.packages import add_wrapped_package
from .functions.request_handler import request_handler

def aikido_middleware_call(flask_app, environ, start_response):
    """
    Aikido WSGI Middleware for ratelimiting and route reporting
    """
    response = request_handler(stage="pre_response")
    if response:
        from flask import jsonify  #  We don't want to install flask

        with flask_app.app_context():
            start_response(f"{response[1]} Aikido", [])
            return [response[0].encode("utf-8")]

    def custom_start_response(status, headers):
        """Is current route useful snippet :"""
        status_code = int(status.split(" ")[0])
        request_handler(stage="post_response", status_code=status_code)
        return start_response(status, headers)

    response = flask_app.wsgi_app(environ, custom_start_response)
    return response

def aikido___call__(flask_app, environ, start_response):
    """Aikido's __call__ wrapper"""
    # We don't want to install werkzeug :
    # pylint: disable=import-outside-toplevel
    try:
        request_handler(stage="init")
        #  https://stackoverflow.com/a/11163649 :
        length = int(environ.get("CONTENT_LENGTH") or 0)
        body = environ["wsgi.input"].read(length)
        # replace the stream since it was exhausted by read()
        environ["wsgi.input"] = BytesIO(body)

        context1 = Context(req=environ, raw_body=body.decode("utf-8"), source="flask")
        logger.debug("Context : %s", json.dumps(context1.__dict__))
        context1.set_as_current_context()
    except Exception as e:
        logger.info("Exception on aikido __call__ function : %s", e)
    return aikido_middleware_call(flask_app, environ, start_response)


@importhook.on_import("flask.app")
def on_flask_import(flask):
    """
    Hook 'n wrap on `flask.app`
    Our goal is to wrap the __init__ function of the "Flask" class,
    so we can insert our middleware. Returns : Modified flask.app object
    """
    modified_flask = importhook.copy_module(flask)
    # pylint: disable=no-member
    setattr(modified_flask.Flask, "__call__", aikido___call__)
    add_wrapped_package("flask")
    return modified_flask
