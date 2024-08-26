"""Exports `process_user`"""


def process_user(reporter, data, queue=None):
    """Adds a user to the users object of the reporter"""
    if reporter:
        reporter.users.add_user(data)
