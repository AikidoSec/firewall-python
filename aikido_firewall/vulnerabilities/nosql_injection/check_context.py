""" Exports `check_context_for_nosql_injection`"""

import json
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
        "metadata": {"filter": json.dumps(_filter)},
        "payload": results["payload"],
    }
