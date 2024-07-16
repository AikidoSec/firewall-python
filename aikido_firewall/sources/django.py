import importhook
import copy
from importlib.metadata import version

AIKIDO_MIDDLEWARE_ADDR = "aikido_firewall.middleware.django.AikidoMiddleware"


@importhook.on_import('django.conf')
def on_django_import(django):
    modified_django = importhook.copy_module(django)
    new_middleware_array = django.settings.MIDDLEWARE + [AIKIDO_MIDDLEWARE_ADDR]

    setattr(modified_django.settings, "MIDDLEWARE", new_middleware_array)
    print("[AIK] Modified Django")
    return modified_django