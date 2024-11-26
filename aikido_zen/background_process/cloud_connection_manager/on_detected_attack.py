"""Mainly exports on_detected_attack"""

import json
from aikido_zen.helpers.get_current_unixtime_ms import get_unixtime_ms
from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.limit_length_metadata import limit_length_metadata
from aikido_zen.helpers.get_ua_from_context import get_ua_from_context
from aikido_zen.helpers.serialize_to_json import serialize_to_json


def on_detected_attack(connection_manager, attack, context, blocked, stack):
    """
    This will send something to the API when an attack is detected
    """
    if not connection_manager.token:
        return
    # Modify attack so we can send it out :
    try:
        attack["user"] = getattr(context, "user", None)
        attack["payload"] = json.dumps(attack["payload"])[:4096]
        attack["metadata"] = limit_length_metadata(attack["metadata"], 4096)
        attack["blocked"] = blocked
        attack["stack"] = stack

        payload = {
            "type": "detected_attack",
            "time": get_unixtime_ms(),
            "agent": connection_manager.get_manager_info(),
            "attack": attack,
            "request": {
                "method": context.method,
                "url": context.url,
                "ipAddress": context.remote_address,
                "userAgent": get_ua_from_context(context),
                "body": context.body,
                "headers": context.headers,
                "source": context.source,
                "route": context.route,
            },
        }
        logger.debug(serialize_to_json(payload))
        result = connection_manager.api.report(
            connection_manager.token,
            payload,
            connection_manager.timeout_in_sec,
        )
        logger.debug("Result : %s", result)
    except Exception as e:
        logger.debug(e)
        logger.info("Failed to report an attack")
