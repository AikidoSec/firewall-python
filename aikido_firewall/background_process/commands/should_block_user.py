"""Mainly exports `process_should_block_user`"""


def process_should_block_user(connection_manager, data, conn):
    """Checks if the user id should be blocked or not"""
    if not connection_manager:
        return conn.send(False)
    should_block = connection_manager.conf.is_user_blocked(data)
    conn.send(should_block)
