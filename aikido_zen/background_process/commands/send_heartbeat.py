from aikido_zen.helpers.logging import logger


def process_send_heartbeat(connection_manager, data, queue):
    """
    SEND_HEARTBEAT: Used by lambdas to flush data.
    """
    logger.debug("SEND_HEARTBEAT start [->]")
    connection_manager.send_heartbeat()
    logger.debug("SEND_HEARTBEAT END [<-]")
    return {"status": "Heartbeat sent"}
