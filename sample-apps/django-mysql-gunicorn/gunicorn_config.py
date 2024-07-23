import aikido_firewall
import json
from urllib.parse import parse_qs
from io import BytesIO
from aikido_firewall.context import Context
from gunicorn.http.body import Body

def when_ready(server):
    aikido_firewall.protect("server-only")

def pre_fork(server, worker):
    pass

def post_fork(server, worker):
    print("----------------------> POST FORK")
    import aikido_firewall
    aikido_firewall.protect("django-gunicorn", False)

def pre_request(worker, req):
    req.body, req.body_copy = clone_body(req.body)

    django_context = Context(req, "django-gunicorn")
    django_context.set_as_current_context()

    worker.log.debug("%s %s", req.method, req.path)


def clone_body(body):
    body_read = body.read()

    # Read the body content into a buffer
    body_buffer = BytesIO()
    body_buffer.write(body_read)
    body_buffer.seek(0)
    
    # Create a new Body object with the same content
    cloned_body = Body(body_buffer)
    
    return (cloned_body, body_read)
