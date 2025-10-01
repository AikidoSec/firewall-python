from aikido_zen.context import Context
from aikido_zen.helpers.get_current_unixtime_ms import get_unixtime_ms
from aikido_zen.helpers.logging import logger


def on_detected_attack_wave(connection_manager, context: Context, metadata):
    if not connection_manager.token:
        return
    try:
        agent_info = connection_manager.get_manager_info()
        payload = create_attack_wave_payload(agent_info, context, metadata)

        connection_manager.api.report(
            connection_manager.token,
            payload,
            connection_manager.timeout_in_sec,
        )
    except Exception as e:
        logger.info("Failed to report an attack wave (%s)", str(e))


def create_attack_wave_payload(agent_info, context: Context, metadata):
    return {
        "type": "detected_attack_wave",
        "time": get_unixtime_ms(),
        "agent": agent_info,
        "attack": {"metadata": metadata, "user": context.user},
        "request": {
            "ipAddress": context.remote_address,
            "userAgent": context.get_user_agent(),
            "source": context.source,
        },
    }
