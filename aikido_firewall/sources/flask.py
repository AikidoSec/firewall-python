"""
Flask source module, intercepts flask import and adds Aikido middleware
"""

import copy
import json
from io import BytesIO
import importhook
from aikido_firewall.helpers.logging import logger
from aikido_firewall.context import Context, get_current_context
from aikido_firewall.background_process import get_comms
from aikido_firewall.helpers.is_useful_route import is_useful_route
from aikido_firewall.errors import AikidoRateLimiting
from aikido_firewall.background_process.packages import add_wrapped_package


class AikidoMiddleware:
    """
    Aikido WSGI Middleware for ratelimiting and route reporting
    """

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        context = get_current_context()
        comms = get_comms()
        if not context or not comms:
            return

        # Ratelimiting snippet :
        ratelimit_res = comms.send_data_to_bg_process(
            action="SHOULD_RATELIMIT", obj=context, receive=True
        )
        if ratelimit_res["success"] and ratelimit_res["data"]["block"]:
            from flask import make_response  #  We don't want to install flask

            message = "You are rate limited by Aikido firewall"
            if ratelimit_res["data"]["trigger"] is "ip":
                message += f" (Your IP: {context.remote_address})"
            return make_response(message, 429)

        def custom_start_response(status, headers):
            """Is current route useful snippet :"""
            status_code = int(status.split(" ")[0])
            is_curr_route_useful = is_useful_route(
                status_code, context.route, context.method
            )
            if is_curr_route_useful:
                comms.send_data_to_bg_process("ROUTE", (context.method, context.route))
            return start_response(status, headers)

        response = self.app(environ, custom_start_response)
        return response


def aikido___call__(flask_app, environ, start_response):
    """Aikido's __call__ wrapper"""
    # We don't want to install werkzeug :
    # pylint: disable=import-outside-toplevel
    try:
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
    res = flask_app.wsgi_app(environ, start_response)
    return res


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
        setattr(_self, "__call__", aikido___call__)
        _self.wsgi_app = AikidoMiddleware(_self.wsgi_app)

    # pylint: disable=no-member
    setattr(modified_flask.Flask, "__init__", aikido_flask_init)
    setattr(modified_flask.Flask, "__call__", aikido___call__)
    add_wrapped_package("flask")
    return modified_flask
