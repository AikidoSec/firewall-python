from aikido_zen.helpers.logging import logger


def extract_body_from_flask_request(req):
    try:
        if req.form:
            return req.form
        return req.data
    except Exception as e:
        logger.debug("Exception occurred whilst extracting flask body data: %s", e)
    return None
