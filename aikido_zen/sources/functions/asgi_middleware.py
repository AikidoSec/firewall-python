from aikido_zen.context import Context
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import before_async, patch_function
from aikido_zen.sources.functions.request_handler import request_handler, post_response
from aikido_zen.thread.thread_cache import get_cache


class InternalASGIMiddleware:
    def __init__(self, app, source: str):
        self.client_app = app
        self.source = source

    async def __call__(self, scope, receive, send):
        if not scope or scope.get("type") != "http":
            # Zen checks requests coming into HTTP(S) server, ignore other requests (like ws)
            return await self.client_app(scope, receive, send)

        context = Context(req=scope, source=self.source)

        process_cache = get_cache()
        if process_cache and process_cache.is_bypassed_ip(context.remote_address):
            # IP address is bypassed, for simplicity we do not set a context,
            # and we do not do any further handling of the request.
            return await self.client_app(scope, receive, send)

        context.set_as_current_context()
        if process_cache:
            # Since this SHOULD be the highest level of the apps we wrap, this is the safest place
            # to increment total hits.
            process_cache.stats.increment_total_hits()

        intercept_response = request_handler(stage="pre_response")
        if intercept_response:
            # The request has already been blocked (e.g. IP is on blocklist)
            return await send_status_code_and_text(send, intercept_response)

        return await self.run_with_intercepts(scope, receive, send)

    async def run_with_intercepts(self, scope, receive, send):
        # We use a skeleton class so we can use patch_function (and the logic already defined in @before_async)
        class InterceptorSkeletonClass:
            @staticmethod
            async def send(*args, **kwargs):
                return await send(*args, **kwargs)

        patch_function(InterceptorSkeletonClass, "send", send_interceptor)

        return await self.client_app(scope, receive, InterceptorSkeletonClass.send)


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


@before_async
async def send_interceptor(func, instance, args, kwargs):
    # There is no name for the send() comment in the standard, it really depends (quart uses message)
    event = get_argument(args, kwargs, 0, name="message")

    # https://asgi.readthedocs.io/en/latest/specs/www.html#response-start-send-event
    if not event or "http.response.start" not in event.get("type", ""):
        # If the event is not of type http.response.start it won't contain the status code.
        # And this event is required before sending over a body (so even 200 status codes are intercepted).
        return

    if "status" in event:
        # Handle post response logic (attack waves, route reporting, ...)
        post_response(status_code=int(event.get("status")))
