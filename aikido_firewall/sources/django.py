"""
Django source module, intercepts django import and adds Aikido middleware
"""
import importhook

AIKIDO_MIDDLEWARE_ADDR = "aikido_firewall.middleware.django.AikidoMiddleware"

@importhook.on_import('django.conf')
def on_django_import(django):
    """
    Hook 'n wrap on `django.conf`
    Our goal here is to wrap the settings object and add our middleware into the list
    Returns : Modified django.conf object
    """
    modified_django = importhook.copy_module(django)
    new_middleware_array = [AIKIDO_MIDDLEWARE_ADDR] + django.settings.MIDDLEWARE

    setattr(modified_django.settings, "MIDDLEWARE", new_middleware_array) # pylint: disable=no-member
    print("[AIK] Modified Django")
    return modified_django
