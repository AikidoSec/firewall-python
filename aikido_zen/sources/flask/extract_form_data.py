from aikido_zen.context import get_current_context
from aikido_zen.helpers.logging import logger


def extract_form_data_from_flask_request_and_save_data(req):
    """Extract form data from flask request"""
    context = get_current_context()
    try:
        if context:
            if req.form:
                context.set_body(req.form)
            else:
                context.set_body(req.data.decode("utf-8"))
            context.set_as_current_context()
    except Exception as e:
        logger.debug("Exception occurred whilst extracting flask body data: %s", e)
