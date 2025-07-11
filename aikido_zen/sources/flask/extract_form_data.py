from aikido_zen.context import get_current_context
from aikido_zen.helpers.logging import logger


def extract_form_data_from_flask_request_and_save_data(req):
    """Extract form data from flask request"""
    context = get_current_context()
    if not context:
        return
    try:
        # https://flask.palletsprojects.com/en/stable/api/#flask.Request
        # req.form is an ImmutableMultiDict, use `.to_dict(flat=False)` to extract all values.
        if req.form:
            form_data = req.form.to_dict(flat=False)
            context.set_body(form_data)
        else:
            context.set_body(req.data.decode("utf-8"))
        context.set_as_current_context()
    except Exception as e:
        logger.debug("Exception occurred whilst extracting flask body data: %s", e)
