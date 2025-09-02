def process_send_heartbeat(connection_manager, data, queue):
    """
    SEND_HEARTBEAT: Used by lambdas to flush data.
    """
    connection_manager.send_heartbeat()
    return {"status": "Heartbeat sent"}
