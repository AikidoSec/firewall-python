import importhook
from importlib.metadata import version

class AikidoMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        response = self.app(environ, start_response)
        return response

def aikido_flask_init(_self, *args, **kwargs):
        super(_self.__class__, _self).__init__(*args, **kwargs)
        print("Flask version : ", version("flask"))
        _self.wsgi_app = AikidoMiddleware(_self.wsgi_app)

@importhook.on_import('flask')
def on_flask_import(flask):
    modified_flask = importhook.copy_module(flask)
    setattr(modified_flask.Flask, "__init__", aikido_flask_init)
    print("Modified flask")
    return modified_flask