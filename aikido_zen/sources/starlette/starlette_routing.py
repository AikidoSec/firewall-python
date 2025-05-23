from aikido_zen.helpers.logging import logger
from .extract_data_from_request import extract_data_from_request
from ..functions.request_handler import request_handler
from ...sinks import on_import, patch_function, before


def _request_response(func, instance, args, kwargs):
    if kwargs and "func" in kwargs:
        kwargs["func"] = aik_route_func_wrapper(kwargs["func"])
    elif args and args[0]:
        # Modify first element of a tuple, tuples are immutable
        args = (aik_route_func_wrapper(args[0]),) + args[1:]

    return func(*args, **kwargs)  # Call the original function


@on_import("starlette.routing", "starlette")
def patch(m):
    """
    patching module starlette.routing (for initial request_handler)
    - patches: request_response
    (github src: https://github.com/encode/starlette/blob/4acf1d1ca3e8aa767567cb4e6e12f093f066553b/starlette/routing.py#L58)
    """
    patch_function(m, "request_response", _request_response)


def aik_route_func_wrapper(func):
    async def aikido_route_func(*args, **kwargs):
        # Code before response (pre_response stage)
        try:
            req = args[0]
            if not req:
                return
            await extract_data_from_request(req)
            pre_response_results = request_handler(stage="pre_response")
            if pre_response_results:
                response = create_starlette_response(pre_response_results)
                if response:
                    # Make sure to not return when an error occurred or there is an invalid response
                    return response
        except Exception as e:
            logger.debug("Exception occurred in pre_response stage starlette : %s", e)

        # Calling the function, check if it's async or not (same checks as in codebase starlette)
        try:
            import functools
            from starlette.concurrency import run_in_threadpool
            from starlette._utils import is_async_callable
        except ImportError:
            logger.info("Make sure starlette install OK : .concurrency, ._utils")
            return await func(*args, **kwargs)
        res = None
        if is_async_callable(func):
            res = await func(*args, **kwargs)
        else:
            # `func` provided by the end-user is allowed to be both synchronous and asynchronous
            # Here we convert sync functions in the same way the starlette codebase does to ensure
            # there are no compatibility issues and the behaviour remains unchanged.
            res = await functools.partial(run_in_threadpool, func)(*args, **kwargs)

        # Code after response (post_response stage)
        request_handler(stage="post_response", status_code=res.status_code)
        return res

    return aikido_route_func


def create_starlette_response(pre_response):
    """Tries to import PlainTextResponse and generates starlette plain text response"""
    text, status_code = pre_response
    try:
        from starlette.responses import PlainTextResponse
    except ImportError:
        logger.info(
            "Ensure `starlette` install is valid, failed to import starlette.responses"
        )
        return None
    return PlainTextResponse(text, status_code)
