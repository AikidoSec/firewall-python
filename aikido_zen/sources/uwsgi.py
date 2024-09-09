"""UWSGI Module, report if module was found"""

import aikido_zen.importhook as importhook
from aikido_zen.background_process.packages import add_wrapped_package


@importhook.on_import("uwsgi")
def on_uwsgi_import(uwsgi):
    """Report to the core when uwsgi gets imported"""
    add_wrapped_package("uwsgi")
    return uwsgi