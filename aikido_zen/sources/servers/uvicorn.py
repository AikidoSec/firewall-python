from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import before, on_import, patch_function
from aikido_zen.helpers.logging import logger
from aikido_zen.sources.functions.asgi_middleware import InternalASGIMiddleware


@before
def _init(func, instance, args, kwargs):
    config = get_argument(args, kwargs, 0, "config")
    if not config.app:
        return
    logger.debug("Server detected as: Uvicorn, Wrapping ASGI app with Zen.")
    config.app = InternalASGIMiddleware(config.app, "uvicorn")

@on_import("uvicorn.server", "uvicorn")
def patch(m):
    """
    We patch uvicorn.server, so that we can modify the app to go through our ASGI middleware first
    """
    patch_function(m, "Server.__init__", _init)
