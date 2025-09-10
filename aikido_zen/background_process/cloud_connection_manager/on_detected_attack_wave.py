from aikido_zen.context import Context
from aikido_zen.helpers.get_current_unixtime_ms import get_unixtime_ms
from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.serialize_to_json import serialize_to_json


def on_detected_attack_wave(connection_manager, context: Context, metadata):
    if not connection_manager.token:
        return
    try:
        payload = {
            "type": "detected_attack_wave",
            "time": get_unixtime_ms(),
            "agent": connection_manager.get_manager_info(),
            "attack": {"metadata": metadata, "user": context.user},
            "request": {
                "ipAddress": context.remote_address,
                "userAgent": context.get_user_agent(),
                "source": context.source,
            },
        }
        logger.debug(serialize_to_json(payload))
        connection_manager.api.report(
            connection_manager.token,
            payload,
            connection_manager.timeout_in_sec,
        )
    except Exception as e:
        logger.debug(e)
        logger.info("Failed to report an attack wave")
