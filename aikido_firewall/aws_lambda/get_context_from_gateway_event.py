"""Exports get_context_from_gateway_event"""

from aikido_firewall.helpers.try_parse_as_json import try_parse_as_json
from aikido_firewall.context.parse_cookies import parse_cookies


def normalize_headers(headers):
    """Normalize headers to a consistent format."""
    return {k.lower(): v for k, v in headers.items()}


def is_json_content_type(content_type):
    """Check if the content type is JSON."""
    return content_type.lower() == "application/json"


def parse_body(event):
    """Parse the body of an API Gateway event."""
    headers = normalize_headers(event.get("headers", {}))

    if not event.get("body") or not is_json_content_type(
        headers.get("content-type", "")
    ):
        return None

    return try_parse_as_json(event["body"])


def get_context_from_gateway_event(event):
    """Gets a context json from the provided gateway event"""
    remote_address = event.get("requestContext", {}).get("identity", {}).get("sourceIp")
    return {
        "url": None,
        "method": event.get("httpMethod"),
        "remoteAddress": remote_address,
        "body": parse_body(event),
        "headers": event.get("headers", {}),
        "routeParams": event.get("pathParameters", {}),
        "query": event.get("queryStringParameters", {}),
        "cookies": parse_cookies(event.get("headers", {}).get("cookie")),
        "source": "lambda/gateway",
        "route": event.get("resource"),
    }
