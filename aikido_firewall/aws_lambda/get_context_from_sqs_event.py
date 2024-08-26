"""Exports get_context_from_sqs_event"""

from aikido_firewall.helpers.try_parse_as_json import try_parse_as_json


def get_context_from_sqs_event(event):
    """Gets the context from an sqs event"""
    body = []
    for record in event.get("Records", []):
        parsed_record = try_parse_as_json(record.get("Body", "{}"))
        if parsed_record:
            body.append(parsed_record)
    return {
        "url": None,
        "method": None,
        "remoteAddress": None,
        "body": {
            "Records": [{"body": record} for record in body],
        },
        "routeParams": {},
        "headers": {},
        "query": {},
        "cookies": {},
        "source": "lambda/sqs",
        "route": None,
    }
