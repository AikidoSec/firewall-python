"""Exports ratelimiting and user blocking middleware for ASGI"""

from aikido_zen.helpers.logging import logger
from .should_block_request import should_block_request


class AikidoASGIMiddleware:
    """Ratelimiting and user blocking middleware for ASGI"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        result = should_block_request()
        if result["block"] is not True:
            return await self.app(scope, receive, send)

        if result["type"] == "ratelimited":
            message = "You are rate limited by Zen."
            if result["trigger"] == "ip" and result["ip"]:
                message += " (Your IP: " + result["ip"] + ")"
            headers = {}
            if result["retry_after_seconds"]:
                headers["Retry-After"] = str(result["retry_after_seconds"])
            return await send_status_code_and_text(send, (message, 429), headers)

        if result["type"] == "blocked":
            return await send_status_code_and_text(
                send, ("You are blocked by Zen.", 403)
            )

        logger.debug("Unknown type for blocking request: %s", result["type"])
        return await self.app(scope, receive, send)


async def send_status_code_and_text(send, pre_response, headers=None):
    """Sends a status code and text"""
    raw_headers = [(b"content-type", b"text/plain")]
    for name, value in (headers or {}).items():
        # ASGI requires lowercase header names as bytes.
        raw_headers.append((name.lower().encode(), value.encode()))
    await send(
        {
            "type": "http.response.start",
            "status": pre_response[1],
            "headers": raw_headers,
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": pre_response[0].encode("utf-8"),
            "more_body": False,
        }
    )
