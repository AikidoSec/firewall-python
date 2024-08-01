"""
Includes all the wrappers for gunicorn config file
"""

from gunicorn.http.body import Body
from io import BytesIO
import aikido_firewall
from aikido_firewall.context import Context, get_current_context
from aikido_firewall.helpers.is_usefull_route import is_usefull_route
from aikido_firewall.background_process import get_comms


RATELIMIT_BLOCK_MSG = "You are rate limited by Aikido firewall."


def when_ready(prev_func):
    """
    Aikido decorator for gunicorn config
    Function: pre_request(worker, req)
    """

    def aik_when_ready(server):
        aikido_firewall.protect("background-process-only")
        prev_func(server)

    return aik_when_ready


def pre_request(prev_func):
    """
    Aikido decorator for gunicorn config
    Function: pre_request(worker, req)
    """

    def aik_pre_request(worker, req):
        req.body, req.body_copy = clone_body(req.body)

        django_context = Context(req=req, source="django-gunicorn")
        django_context.set_as_current_context()
        prev_func(worker, req)

    return aik_pre_request


def post_request(prev_func):
    """
    Aikido decorator for gunicorn config
    Function: post_request(worker, req, environ, resp)
    """

    def aik_post_request(worker, req, environ, resp):
        context = get_current_context()
        if not context:
            return prev_func(worker, req, environ, resp)
        print(resp.__dict__)
        comms = get_comms()

        is_curr_route_usefull = is_usefull_route(
            resp.status_code, context.route, context.method
        )
        if is_curr_route_usefull:
            comms.send_data_to_bg_process("ROUTE", (context.method, context.route))
        # comms.send_data_to_bg_process("STATS:ADD_REQ", ())

        ratelimit = comms.send_data_to_bg_process("RLM:SHOULD_RLM", context, True)
        if ratelimit and ratelimit.get("block"):
            raise EnvironmentError(RATELIMIT_BLOCK_MSG)

        prev_func(worker, req, environ, resp)

    return aik_post_request


def post_fork(prev_func):
    """
    Aikido decorator for gunicorn config
    Function: post_fork(server, worker)
    """

    def aik_post_fork(server, worker):
        aikido_firewall.protect("django-gunicorn", False)
        prev_func(server, worker)

    return aik_post_fork


def clone_body(body):
    """
    Clones the body by creating a new stream
    """
    body_read = body.read()

    # Read the body content into a buffer
    body_buffer = BytesIO()
    body_buffer.write(body_read)
    body_buffer.seek(0)

    # Create a new Body object with the same content
    cloned_body = Body(body_buffer)

    return (cloned_body, body_read)
