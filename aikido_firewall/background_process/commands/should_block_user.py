"""Mainly exports `process_should_block_user`"""


def process_should_block_user(connection_manager, data, conn, queue=None):
    """Checks if the user id should be blocked or not"""
    if not connection_manager:
        return False
    return connection_manager.conf.is_user_blocked(data)
