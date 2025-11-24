import json

from aikido_zen.helpers.limit_length_metadata import limit_length_metadata
from aikido_zen.helpers.logging import logger


def create_detected_attack_api_event(attack, context, blocked, stack):
    try:
        return {
            "type": "detected_attack",
            "attack": {
                **attack,
                "user": getattr(context, "user", None),
                "payload": json.dumps(attack["payload"])[:4096],
                "metadata": limit_length_metadata(attack["metadata"], 4096),
                "blocked": blocked,
                "stack": stack,
            },
            "request": extract_request_if_possible(context),
        }
    except Exception as e:
        logger.error("Failed to create detected_attack API event: %s", str(e))
        return None


def extract_request_if_possible(context):
    if not context:
        return None
    return {
        "method": getattr(context, "method", None),
        "url": getattr(context, "url", None),
        "ipAddress": getattr(context, "remote_address", None),
        "source": getattr(context, "source", None),
        "route": getattr(context, "route", None),
        "userAgent": context.get_user_agent(),
    }
