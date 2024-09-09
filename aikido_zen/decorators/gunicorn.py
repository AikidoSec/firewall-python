"""
Includes all the wrappers for gunicorn config file
"""

import aikido_zen


# Run our background process as a child of gunicorn (exits safely)
aikido_zen.protect("daemon_only")


def post_fork(prev_func):
    """
    Aikido decorator for gunicorn config
    Function: post_fork(server, worker)
    """

    def aik_post_fork(server, worker):
        aikido_zen.protect("daemon_disabled")
        prev_func(server, worker)

    return aik_post_fork
