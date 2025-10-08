"""
Includes all the wrappers for gunicorn config file
"""

import aikido_zen


def post_fork(prev_func):
    """
    Aikido decorator for gunicorn config
    Function: post_fork(server, worker)
    """

    def aik_post_fork(server, worker):
        aikido_zen.protect()
        prev_func(server, worker)

    return aik_post_fork
