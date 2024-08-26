"""Mainly exports `process_should_block_user`"""


def process_should_block_user(reporter, data, conn):
    """Checks if the user id should be blocked or not"""
    if not reporter:
        return conn.send(False)
    should_block = reporter.conf.is_user_blocked(data)
    conn.send(should_block)
