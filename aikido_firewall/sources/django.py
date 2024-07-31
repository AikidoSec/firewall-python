"""
Django source module, intercepts django import and adds Aikido middleware
"""

import importhook
from aikido_firewall.helpers.logging import logger


AIKIDO_MIDDLEWARE_ADDR = "aikido_firewall.middleware.django.AikidoMiddleware"


@importhook.on_import("django.conf")
def on_django_import(django):
    """
    Hook 'n wrap on `django.conf`
    Our goal here is to wrap the settings object and add our middleware into the list
    Returns : Modified django.conf object
    """
    modified_django = importhook.copy_module(django)
    new_middleware_array = [AIKIDO_MIDDLEWARE_ADDR] + django.settings.MIDDLEWARE

    # pylint: disable=no-member
    setattr(modified_django.settings, "MIDDLEWARE", new_middleware_array)
    logger.info("Wrapped `django` module")
    return modified_django
