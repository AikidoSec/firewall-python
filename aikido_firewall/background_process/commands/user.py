"""Exports `process_user`"""


def process_user(bg_process, data, conn):
    """Adds a user to the users object of the reporter"""
    if bg_process.reporter:
        bg_process.reporter.users.add_user(data)
