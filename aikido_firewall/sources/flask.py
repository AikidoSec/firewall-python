"""
Flask source module, intercepts flask import and adds Aikido middleware
"""

import copy
from importlib.metadata import version
import importhook
from flask_http_middleware import MiddlewareManager, BaseHTTPMiddleware
from aikido_firewall.helpers.logging import logger
from aikido_firewall.context import Context
from aikido_firewall.background_process import get_comms
from aikido_firewall.helpers.is_usefull_route import is_usefull_route

RATELIMIT_BLOCK_MSG = "You are rate limited by Aikido firewall."


class AikidoMiddleware(BaseHTTPMiddleware):  # pylint: disable=too-few-public-methods
    """
    Aikido WSGI Middleware | uses headers, body, etc. as sources
    """

    def __init__(self):
        super().__init__()

    def dispatch(self, request, call_next):
        """Dispatch function"""
        logger.debug("Aikido middleware for `flask` was called")
        context = Context(req=request, source="flask")
        context.set_as_current_context()

        response = call_next(request)
        if not context or not context.route or not context.method:
            return response
        comms = get_comms()

        is_curr_route_usefull = is_usefull_route(
            response._status_code, context.route, context.method
        )
        if is_curr_route_usefull:
            comms.send_data_to_bg_process("ROUTE", (context.method, context.route))
        # comms.send_data_to_bg_process("STATS:ADD_REQ", ())

        ratelimit = comms.send_and_recv_from_bg_process("RLM:SHOULD_RLM", context)
        if ratelimit.block:
            raise EnvironmentError(RATELIMIT_BLOCK_MSG)

        return response


@importhook.on_import("flask.app")
def on_flask_import(flask):
    """
    Hook 'n wrap on `flask.app`
    Our goal is to wrap the __init__ function of the "Flask" class,
    so we can insert our middleware. Returns : Modified flask.app object
    """
    modified_flask = importhook.copy_module(flask)

    prev_flask_init = copy.deepcopy(flask.Flask.__init__)

    def aikido_flask_init(_self, *args, **kwargs):
        prev_flask_init(_self, *args, **kwargs)
        logger.debug("Wrapper - `flask` version : %s", version("flask"))
        _self.wsgi_app = MiddlewareManager(_self)
        _self.wsgi_app.add_middleware(AikidoMiddleware)

    # pylint: disable=no-member
    setattr(modified_flask.Flask, "__init__", aikido_flask_init)
    logger.debug("Wrapped `flask` module")
    return modified_flask
