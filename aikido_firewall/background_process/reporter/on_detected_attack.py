"""Mainly exports on_detected_attack"""

import json
from aikido_firewall.helpers.get_current_unixtime_ms import get_unixtime_ms
from aikido_firewall.helpers.logging import logger
from aikido_firewall.helpers.limit_length_metadata import limit_length_metadata
from aikido_firewall.helpers.get_ua_from_context import get_ua_from_context


def on_detected_attack(reporter, attack, context):
    """
    This will send something to the API when an attack is detected
    """
    if not reporter.token:
        return
    # Modify attack so we can send it out :
    try:
        attack["user"] = None
        attack["payload"] = json.dumps(attack["payload"])[:4096]
        attack["metadata"] = limit_length_metadata(attack["metadata"], 4096)
        attack["blocked"] = reporter.block

        payload = {
            "type": "detected_attack",
            "time": get_unixtime_ms(),
            "agent": reporter.get_reporter_info(),
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
        logger.debug(json.dumps(payload))
        result = reporter.api.report(
            reporter.token,
            payload,
            reporter.timeout_in_sec,
        )
        logger.debug("Result : %s", result)
    except Exception as e:
        logger.debug(e)
        logger.info("Failed to report an attack")
