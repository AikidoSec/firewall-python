import aikido_zen.decorators.gunicorn as aik
@aik.post_fork
def post_fork(server, worker): pass

# ASGI-specific configuration
worker_class = 'uvicorn.workers.UvicornWorker'
