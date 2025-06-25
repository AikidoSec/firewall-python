from aikido_zen.context import get_current_context
from aikido_zen.helpers.logging import logger


def extract_view_args_from_flask_request_and_save_data(req):
    """Extract view args from flask request"""
    context = get_current_context()

    try:
        if getattr(req, "view_args"):
            context.route_params = dict(req.view_args)
            context.set_as_current_context()
    except Exception as e:
        logger.debug("Exception occurred whilst extracting flask view args data: %s", e)
