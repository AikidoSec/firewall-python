"""UWSGI Module, report if module was found"""

import aikido_zen.importhook as importhook
from aikido_zen.background_process.packages import pkg_compat_check, ANY_VERSION


@importhook.on_import("uwsgi")
def on_uwsgi_import(uwsgi):
    """Report to the core when uwsgi gets imported"""
    pkg_compat_check("uwsgi", required_version=ANY_VERSION)
    return uwsgi
