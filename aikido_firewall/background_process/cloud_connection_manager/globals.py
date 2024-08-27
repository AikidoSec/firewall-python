"""Globals file for cloud_connection_manager"""

# Global variable to hold the cloud connection manager instance
global_cloud_connection_manager = None  # pylint: disable=invalid-name


def get_global_cloud_connection_manager():
    """Retrieve the current global cloud connection manager.

    Returns:
        The current cloud connection manager instance, or None if not set.
    """
    return global_cloud_connection_manager


def set_global_cloud_connection_manager(connection_manager):
    """Set the global cloud connection manager.

    Args:
        connection_manager: An instance of the cloud connection manager to set as global.
    """
    global global_cloud_connection_manager  # pylint: disable=global-statement
    global_cloud_connection_manager = connection_manager
