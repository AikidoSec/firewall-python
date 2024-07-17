"""
Flask source module, intercepts flask import and adds Aikido middleware
"""

import copy
from importlib.metadata import version
import importhook
from aikido_firewall.helpers.logging import logger
from aikido_firewall.context import Context


class AikidoMiddleware:  # pylint: disable=too-few-public-methods
    """
    Aikido WSGI Middleware | uses headers, body, etc. as sources
    """

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        logger.debug("Aikido middleware for `flask` was called")
        context = Context(environ)
        logger.debug(context)
        response = self.app(environ, start_response)
        return response


@importhook.on_import("flask.app")
def on_flask_import(flask):
    """
    Hook 'n wrap on `flask.app`
    Our goal is to wrap the __init__ function of the "Flask" class, so we can insert our middleware
    Returns : Modified flask.app object
    """
    modified_flask = importhook.copy_module(flask)

    prev_flask_init = copy.deepcopy(flask.Flask.__init__)

    def aikido_flask_init(_self, *args, **kwargs):
        prev_flask_init(_self, *args, **kwargs)
        logger.debug("Wrapper - `flask` version : %s", version("flask"))
        _self.wsgi_app = AikidoMiddleware(_self.wsgi_app)

    # pylint: disable=no-member
    setattr(modified_flask.Flask, "__init__", aikido_flask_init)
    logger.debug("Wrapped `flask` module")
    return modified_flask
