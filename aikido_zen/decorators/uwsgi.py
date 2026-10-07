"""
Includes all the wrappers for uwsgi apps
"""

import aikido_zen


def postfork(prev_func):
    """
    Aikido decorator for uwsgi's @postfork hook (from uwsgidecorators)
    Function: postfork()
    """

    def aik_postfork():
        aikido_zen.protect()
        prev_func()

    return aik_postfork
