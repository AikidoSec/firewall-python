"""Mainly exports `process_should_block_user`"""


def process_should_block_user(reporter, data, queue=None):
    """Checks if the user id should be blocked or not"""
    if not reporter:
        return False
    should_block = reporter.conf.is_user_blocked(data)
    return should_block
