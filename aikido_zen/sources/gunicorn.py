"""Gunicorn Module, report if module was found"""

import aikido_zen.importhook as importhook
from aikido_zen.background_process.packages import pkg_compat_check, ANY_VERSION


@importhook.on_import("gunicorn")
def on_gunicorn_import(gunicorn):
    """Report to the core when gunicorn gets imported"""
    pkg_compat_check("gunicorn", required_version=ANY_VERSION)
    return gunicorn
