"""
Exports a WSGIContext class that can change a WSGIRequest to 
a context object.
"""
import json
from . import Context
from aikido_firewall.helpers.logging import logger

def extract_wsgi_headers(request):
    """
    Extracts headers out of WSGIRequest
    """
    headers = {}
    for k, v in request.META:
        if k.startswith("HTTP_"):
            headers[k[5:]] = v
    return headers

def wsgi_request_to_context(request, source="WSGI"):
    context1 = Context(req=request, source="django")
    logger.debug("Context : %s", json.dumps(context1.__dict__))
    """
    context_obj = {
        "method": request.METHOD,
        "remote_address": request.REMOTE_ADDR,
        "url":request.RAW_URI,
        "body": {},
        "source": source,
        "headers": extract_wsgi_headers(request),
        "query": request.QUERY_STRING,
        "cookies": request.COOKIES,
        "route": "",
        "subdomains": [],
        "user": None,
    }
    logger.debug("Context object : %s", context_obj)
    context = Context(context_obj)
    """
