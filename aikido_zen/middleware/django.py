"""Exports AikidoDjangoMiddleware"""

from aikido_zen.helpers.logging import logger
from .should_block_request import should_block_request


class AikidoDjangoMiddleware:
    """Middleware for rate-limiting and user blocking for django"""

    def __init__(self, get_response):
        logger.critical("Django middleware ised")
        self.get_response = get_response
        try:
            from django.http import HttpResponse

            self.HttpResponse = HttpResponse
        except ImportError:
            logger.warning(
                "django.http import not working, aikido rate-limiting middleware not running."
            )

    def __call__(self, request):
        result = should_block_request()
        if result["block"] is not True or self.HttpResponse is None:
            return self.get_response(request)

        if result["type"] == "ratelimited":
            message = "You are rate limited by Zen."
            if result["trigger"] == "ip" and result["ip"]:
                message += " (Your IP: " + result["ip"] + ")"
            return self.HttpResponse(message, content_type="text/plain", status=429)
        elif result["type"] == "blocked":
            return self.HttpResponse(
                "You are blocked by Zen.", content_type="text/plain", status=403
            )
        logger.debug("Unknown type for blocking request: %s", result["type"])
        return self.get_response(request)
