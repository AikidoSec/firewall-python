import aikido_firewall.middleware.django_gunicorn as aik
@aik.when_ready
def when_ready(server): pass
@aik.post_fork
def post_fork(server, worker): pass
