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



@importhook.on_import('django.core')
def on_django_import(django):
    modified_django = importhook.copy_module(django)

    #prev_django_init = copy.deepcopy(django.django.__init__)
    #def aikido_django_init(_self, *args, **kwargs):
    #    prev_django_init(_self, *args, **kwargs)
    #    print("[AIK] django version : ", version("django"))
    #    _self.wsgi_app = AikidoMiddleware(_self.wsgi_app)
    
    #setattr(modified_django.django, "__init__", aikido_django_init)
    print("[AIK] Modified Django")
    return modified_django