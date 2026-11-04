"""
Set up Zen in two steps:
1. Install instrumentation when the decorator is applied.
2. Start the background process from uWSGI's postfork hook.
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
