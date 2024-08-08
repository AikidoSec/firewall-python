"""
Includes all the wrappers for gunicorn config file
"""
import aikido_firewall


def when_ready(prev_func):
    """
    Aikido decorator for gunicorn config
    Function: pre_request(worker, req)
    """

    def aik_when_ready(server):
        aikido_firewall.protect("background-process-only")
        prev_func(server)

    return aik_when_ready

def post_fork(prev_func):
    """
    Aikido decorator for gunicorn config
    Function: post_fork(server, worker)
    """

    def aik_post_fork(server, worker):
        aikido_firewall.protect("django-gunicorn", False)
        prev_func(server, worker)

    return aik_post_fork
