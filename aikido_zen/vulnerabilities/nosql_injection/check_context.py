""" Exports `check_context_for_nosql_injection`"""

from aikido_zen.helpers.serialize_to_json import serialize_to_json
from . import detect_nosql_injection


def check_context_for_nosql_injection(context, op, _filter):
    """Checks the context object for a nosql injection"""
    results = detect_nosql_injection(context, _filter)
    if not results or not results["injection"]:
        return {}
    return {
        "operation": op,
        "kind": "nosql_injection",
        "source": results["source"],
        "pathToPayload": results["pathToPayload"],
        "metadata": {"filter": serialize_to_json(_filter)},
        "payload": results["payload"],
    }
