import aikido_zen.decorators.gunicorn as aik

workers = 4
worker_class = "gevent"
worker_connections = 1000
timeout = 30

@aik.post_fork
def post_fork(server, worker): pass
