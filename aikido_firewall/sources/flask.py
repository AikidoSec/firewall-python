"""
Flask source module, intercepts flask import and adds Aikido middleware
"""

import copy
from importlib.metadata import version
import logging
import importhook


class AikidoMiddleware:  # pylint: disable=too-few-public-methods
    """
    Aikido WSGI Middleware | uses headers, body, etc. as sources
    """

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        logging.critical("[AIK] Aikido middleware is working")
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
        print("[AIK] Flask version : ", version("flask"))
        _self.wsgi_app = AikidoMiddleware(_self.wsgi_app)
        print(_self)

    # pylint: disable=no-member
    setattr(modified_flask.Flask, "__init__", aikido_flask_init)
    print("[AIK] Modified flask")
    return modified_flask
