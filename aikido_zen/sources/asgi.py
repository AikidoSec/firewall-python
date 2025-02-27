from aikido_zen import logger
from aikido_zen.context import Context
from aikido_zen.sources.functions.on_init_handler import on_init_handler


def asgi_decorator(func, source):
    """
    ASGI Decorator: Creates context object, adds hits and checks for blocking (e.g. geo restrictions)
    """

    async def wrapper(self, scope, receive, send):
        try:
            if scope["type"] != "http":
                return await func(self, scope, receive, send)

            block_result = on_init_handler(Context(req=scope, source=source))
            if block_result.blocking:
                # We need to write a response and stop further processing :
                await send(
                    {
                        "type": "http.response.start",
                        "status": block_result.status_code,
                        "headers": [(b"content-type", b"text/plain")],
                    }
                )
                await send(
                    {
                        "type": "http.response.body",
                        "body": block_result.message.encode("utf-8"),
                        "more_body": False,
                    }
                )
                return  # Stop any further processing

        except Exception as e:
            logger.debug("ASGI decorator exception : %s", e)
        return await func(self, scope, receive, send)

    return wrapper
