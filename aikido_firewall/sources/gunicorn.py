"""Gunicorn Module, report if module was found"""

import importhook
from aikido_firewall.background_process.packages import add_wrapped_package


@importhook.on_import("gunicorn")
def on_gunicorn_import(gunicorn):
    """Report to the core when gunicorn gets imported"""
    add_wrapped_package("gunicorn")
    return gunicorn
