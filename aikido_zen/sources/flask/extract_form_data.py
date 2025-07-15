from typing import Dict, List

from aikido_zen.context import get_current_context
from aikido_zen.helpers.logging import logger


def extract_form_data_from_flask_request_and_save_data(req):
    """Extract form data from flask request"""
    context = get_current_context()
    if not context:
        return
    try:
        # https://flask.palletsprojects.com/en/stable/api/#flask.Request
        # req.form is an ImmutableMultiDict, we will try and extract all values for a certain key
        if req.form:
            form_data: Dict[str, List] = {}

            # Extract to a dict of lists
            for key, value in req.form.items(multi=True):
                if not key in form_data:
                    form_data[key] = list()
                form_data[key].append(value)

            context.set_body(form_data)
        else:
            context.set_body(req.data.decode("utf-8"))
        context.set_as_current_context()
    except Exception as e:
        logger.debug("Exception occurred whilst extracting flask body data: %s", e)
