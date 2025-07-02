"""Exports get_body_data_type"""

from aikido_zen.helpers.headers import Headers

JSON_CONTENT_TYPES = [
    "application/json",
    "application/vnd.api+json",
    "application/csp-report",
    "application/x-json",
]


def get_body_data_type(headers: Headers):
    """Gets the type of body data from headers"""
    if not isinstance(headers, Headers) or headers is None:
        return

    content_type = headers.get_header("CONTENT_TYPE")
    if not content_type:
        return

    if isinstance(content_type, list):
        # Choose the first content type if there are multiple
        content_type = content_type[0]

    if any(json_type in content_type for json_type in JSON_CONTENT_TYPES):
        return "json"

    if content_type.startswith("application/x-www-form-urlencoded"):
        return "form-urlencoded"

    if content_type.startswith("multipart/form-data"):
        return "form-data"

    if "xml" in content_type:
        return "xml"

    return None
