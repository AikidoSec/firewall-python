"""Exports `process_user`"""


def process_user(connection_manager, data, conn):
    """Adds a user to the users object of the connection_manager"""
    if connection_manager:
        connection_manager.users.add_user(data)
