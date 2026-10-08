"""
Includes all the wrappers for uwsgi apps
"""

import aikido_zen


def postfork(prev_func):
    """
    Aikido decorator for uwsgi's @postfork hook (from uwsgidecorators)
    Function: postfork()
    """

    aikido_zen.protect(mode="daemon_disabled")

    def aik_postfork():
        aikido_zen.protect(mode="daemon_only")
        prev_func()

    return aik_postfork
