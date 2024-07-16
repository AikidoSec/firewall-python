import importhook
import copy
from importlib.metadata import version

class AikidoMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        print("[AIK] Aikido middleware is working")
        response = self.app(environ, start_response)
        return response



@importhook.on_import('flask')
def on_flask_import(flask):
    modified_flask = importhook.copy_module(flask)

    prev_flask_init = copy.deepcopy(flask.Flask.__init__)
    def aikido_flask_init(_self, *args, **kwargs):
        prev_flask_init(_self, *args, **kwargs)
        print("[AIK] Flask version : ", version("flask"))
        _self.wsgi_app = AikidoMiddleware(_self.wsgi_app)
    
    setattr(modified_flask.Flask, "__init__", aikido_flask_init)
    print("[AIK] Modified flask")
    return modified_flask