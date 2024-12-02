"""Exports ratelimiting and user blocking middleware for Flask"""

from aikido_zen.helpers.logging import logger
from .should_block_request import should_block_request


class AikidoFlaskMiddleware:
    """Ratelimiting and user blocking middleware for Flask"""

    def __init__(self, app):
        self.app = app
        try:
            from werkzeug.wrappers import Response

            self.Response = Response
        except ImportError:
            logger.warning(
                "Something went wrong whilst importing werkzeug.wrappers, middleware does not work"
            )

    def __call__(self, environ, start_response):
        result = should_block_request()
        if result["block"] is not True or self.Response is None:
            return self.app(environ, start_response)

        if result["type"] == "ratelimited":
            message = "You are rate limited by Zen."
            if result["trigger"] == "ip" and result["ip"]:
                message += " (Your IP: " + result["ip"] + ")"
            res = self.Response(message, mimetype="text/plain", status=429)
            return res(environ, start_response)
        elif result["type"] == "blocked":
            res = self.Response(
                "You are blocked by Zen.", mimetype="text/plain", status=403
            )
            return res(environ, start_response)
        logger.debug("Unknown type for blocking request: %s", result["type"])
        return self.app(environ, start_response)
