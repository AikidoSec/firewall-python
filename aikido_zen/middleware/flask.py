from . import should_block_request
from werkzeug.wrappers import Response


class AikidoMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        result = should_block_request()
        if result["block"] is not True:
            return self.app(environ, start_response)

        if result["type"] == "ratelimited":
            message = "You are rate limited by Zen."
            if result["trigger"] == "ip" and result["ip"]:
                message += " (Your IP: " + result["ip"] + ")"
            res = Response(message, mimetype="text/plain", status=429)
            return res(environ, start_response)
        elif result["type"] == "blocked":
            res = Response("You are blocked by Zen.", mimetype="text/plain", status=403)

        return self.app(environ, start_response)
