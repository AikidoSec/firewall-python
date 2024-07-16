import importhook
import copy
from importlib.metadata import version

AIKIDO_MIDDLEWARE_ADDR = "aikido_firewall.middleware.django.AikidoMiddleware"

# Hook 'n wrap on `django.conf`
# Our goal here is to wrap the settings object and add our middleware into the list
@importhook.on_import('django.conf')
def on_django_import(django):
    modified_django = importhook.copy_module(django)
    new_middleware_array = [AIKIDO_MIDDLEWARE_ADDR] + django.settings.MIDDLEWARE

    setattr(modified_django.settings, "MIDDLEWARE", new_middleware_array)
    print("[AIK] Modified Django")
    return modified_django