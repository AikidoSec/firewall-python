"""Mainly exports `process_should_block_user`"""


def process_should_block_user(bg_process, data, conn):
    """Checks if the user id should be blocked or not"""
    should_block = bg_process.reporter.conf.is_user_blocked(data)
    conn.send(should_block)
