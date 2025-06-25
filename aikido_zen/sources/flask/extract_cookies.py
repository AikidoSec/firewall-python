from aikido_zen.context import get_current_context
from aikido_zen.helpers.logging import logger


def extract_cookies_from_flask_request_and_save_data(req):
    """Extract cookies from flask request"""
    context = get_current_context()
    try:
        context.cookies = req.cookies.to_dict()
        context.set_as_current_context()
    except Exception as e:
        logger.debug("Exception occurred whilst extracting flask cookie data: %s", e)
