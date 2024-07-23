import aikido_firewall
import json
def when_ready(server):
    print("----------------------> WHEN READY")
    aikido_firewall.protect("server-only")

def pre_fork(server, worker):
    print("----------------------> PRE FORK")
    #import aikido_firewall.sources.django

def post_fork(server, worker):
    print("----------------------> POST FORK")
    import aikido_firewall
    aikido_firewall.protect("django", False)

def pre_request(worker, req):
    worker.log.critical(req.body)
    from aikido_firewall.context import Context
    django_context = Context(req, "django")
    print(django_context)
    worker.log.debug("%s %s", req.method, req.path)


# Useless : 

def post_worker_init(worker):
    pass

def pre_exec(server):
    pass

def on_reload(server):
    pass

def worker_int(worker):
    pass

def worker_abort(worker):
    pass

def post_request(worker, req, environ, resp):
    pass

def child_exit(server, worker):
    pass

def worker_exit(server, worker):
    pass

def nworkers_changed(server, new_value, old_value):
    pass

def on_exit(server):
    pass

def ssl_context(config, default_ssl_context_factory):
    return default_ssl_context_factory()
