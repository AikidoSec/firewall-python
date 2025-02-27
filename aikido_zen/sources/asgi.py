from aikido_zen import logger
from aikido_zen.context import Context
from aikido_zen.sources.functions.check_if_request_is_blocked import (
    check_if_request_is_blocked,
)
from aikido_zen.sources.functions.request_handler import request_handler


def asgi_decorator(func, source):
    """
    ASGI Decorator: Creates context object, adds hits and checks for blocking (e.g. geo restrictions)
    """

    async def wrapper(self, scope, receive, send):
        try:
            if scope["type"] != "http":
                return await func(self, scope, receive, send)
            # Create context and add hits :
            context = Context(req=scope, source=source)
            context.set_as_current_context()
            request_handler(stage="init")

            # Write response if blocking :
            block_result = check_if_request_is_blocked(context)
            if block_result.blocking:
                return await asgi_send_response(
                    send, block_result.message, block_result.status_code
                )
        except Exception as e:
            logger.debug("ASGI decorator exception : %s", e)
        return await func(self, scope, receive, send)

    return wrapper


async def asgi_send_response(send, message, status_code):
    await send(
        {
            "type": "http.response.start",
            "status": status_code,
            "headers": [(b"content-type", b"text/plain")],
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": message.encode("utf-8"),
            "more_body": False,
        }
    )
