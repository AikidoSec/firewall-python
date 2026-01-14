from aikido_zen.context import Context, get_current_context
from aikido_zen.sinks import before, on_import, patch_function
from aikido_zen.helpers.logging import logger

@before
def _init(func, instance, args, kwargs):
    logger.critical(args)
    logger.critical(kwargs)


@on_import("gunicorn.workers.base", "gunicorn")
def patch(m):
    """

    """
    patch_function(m, "Worker.__init__", _init)
