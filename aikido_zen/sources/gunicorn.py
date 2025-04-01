"""Gunicorn Module, report if module was found"""

import aikido_zen.importhook as importhook
from aikido_zen.background_process.packages import is_package_compatible, ANY_VERSION


@importhook.on_import("gunicorn")
def on_gunicorn_import(gunicorn):
    """Report to the core when gunicorn gets imported"""
    is_package_compatible("gunicorn", required_version=ANY_VERSION)
    return gunicorn
