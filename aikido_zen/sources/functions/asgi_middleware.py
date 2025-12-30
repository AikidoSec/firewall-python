from aikido_zen.context import Context
from aikido_zen.sources.functions.request_handler import request_handler
from aikido_zen.thread.thread_cache import get_cache


class InternalASGIMiddleware:
    def __init__(self, app, source: str):
        self.client_app = app
        self.source = source

    async def __call__(self, scope, receive, send):
        if not scope or scope.get("type") != "http":
            # Zen checks requests coming into HTTP(S) server, ignore other requests (like ws)
            await self.client_app(scope, receive, send)
            return

        context = Context(req=scope, source=self.source)

        process_cache = get_cache()
        if process_cache and process_cache.is_bypassed_ip(context.remote_address):
            # IP address is bypassed, for simplicity we do not set a context,
            # and we do not do any further handling of the request.
            await self.client_app(scope, receive, send)
            return

        context.set_as_current_context()
        if process_cache:
            process_cache.stats.increment_total_hits()

        await self.client_app(scope, receive, send)

    async def send_status_code_and_text(send, pre_response):
        await send(
            {
                "type": "http.response.start",
                "status": pre_response[1],
                "headers": [(b"content-type", b"text/plain")],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": pre_response[0].encode("utf-8"),
                "more_body": False,
            }
        )
