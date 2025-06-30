import json

from aikido_zen.context import get_current_context
from aikido_zen.helpers.logging import logger


def extract_body_from_django_request(request):
    try:
        # Check for request.POST (MultiValueDict)
        form_values = _try_extract_from_multi_value_dict(request)
        if form_values is not None:
            return form_values

        # If we weren't able to extract the form values, try parsing JSON ourselves.
        parsed_json = _try_extract_json_from_raw_body(request)
        if parsed_json is not None:
            return parsed_json

        # We resort to setting the raw body
        raw_body = request.body
        if raw_body is not None and len(raw_body) > 0:
            return raw_body

        # During a GET request, django leaves the body as an empty byte string (e.g. `b''`).
        # When an attack is detected, this body needs to be serialized which would fail.
        # That's why we check the length above, and return None if it's 0
        return None
    except Exception as e:
        logger.debug("Exception occurred whilst extracting Django body data: %s", e)


def _try_extract_from_multi_value_dict(request):
    # try-catch loading of form parameters, this is to fix issue with DATA_UPLOAD_MAX_NUMBER_FIELDS :
    try:
        # We are loading from a QueryDict here, so we have to make sure we get all values.
        form_values = {}
        for key in request.POST.keys():
            form_values[key] = request.POST.getlist(key)

        if len(form_values) > 0:
            return form_values
    except Exception:
        pass


def _try_extract_json_from_raw_body(request):
    if request.content_type != "application/json":
        return None
    try:
        body = json.loads(request.body)
        if len(body) > 0:
            return body
    except Exception:
        pass
