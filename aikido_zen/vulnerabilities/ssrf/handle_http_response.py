"""Exports handle_http_response function"""

from aikido_zen.context import get_current_context
from aikido_zen.helpers.is_redirect_status_code import is_redirect_status_code
from aikido_zen.helpers.try_parse_url import try_parse_url
from .find_hostname_in_context import find_hostname_in_context
from .get_redirect_origin import get_redirect_origin


def normalize_headers(headers):
    """Normalize headers to a consistent format."""
    return {k.lower(): v for k, v in headers.items()}


def handle_http_response(http_response, source):
    """Handles a response object from http"""
    context = get_current_context()
    if not context or not source:
        return
    status_code = http_response.code
    if not status_code or not is_redirect_status_code(status_code):
        #  The status code needs to be a redirect status code
        # Otherwise there is no real danger for SSRF attacks
        return

    raw_headers = getattr(http_response, "headers", {})
    headers = normalize_headers(dict(raw_headers))
    location = headers.get("location", None)
    if not isinstance(location, str):
        return

    parsed_location = try_parse_url(location)
    if not parsed_location:
        return

    add_redirect_to_context(source, parsed_location, context)


def add_redirect_to_context(source, destination, context):
    """
    Adds redirects with user provided hostname / url to the context to prevent
    SSRF attacks with redirects.
    """
    redirect_origin = None

    # Check if the source hostname is in the context - is true if its the first redirect
    # in the chain and the user input is the source
    found = find_hostname_in_context(source.hostname, context, source.port)

    # If the source hostname is not in the context, check if it's a redirect in
    # an already existing chain
    if not found and context.outgoing_req_redirects:
        # Get initial source of the redirect chain (first redirect), if url
        # is part of a redirect chain
        redirect_origin = get_redirect_origin(
            redirects=context.outgoing_req_redirects, url=source
        )

    # Get existing redirects or create a new array
    outgoing_redirects = context.outgoing_req_redirects
    if not outgoing_redirects:
        outgoing_redirects = []

    # If it's 1. a initial redirect with user provided url or 2. a redirect in an existing chain,
    # add it to the context
    if found or redirect_origin:
        outgoing_redirects.append({"source": source, "destination": destination})

        # Update context:
        context.outgoing_req_redirects = outgoing_redirects
        context.set_as_current_context()
