"""Exports `parse_raw_body`"""

import urllib
import json
import cgi
from aikido_firewall.helpers.logging import logger


def parse_raw_body(raw_body, content_type):
    """Parses body based on content type header"""
    try:
        if content_type == "application/x-www-form-urlencoded":
            parsed_body = urllib.parse.parse_qs(raw_body)
        elif content_type == "application/json":
            parsed_body = json.loads(raw_body)
        else:
            form = cgi.FieldStorage(
                fp=raw_body, environ={"REQUEST_METHOD": "POST"}, keep_blank_values=True
            )
            parsed_body = {key: form.getvalue(key) for key in form.keys()}
        return parsed_body
    except Exception as e:
        logger.debug("Exception in parse_raw_body : %s", e)
        return raw_body
