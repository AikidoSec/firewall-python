from aikido_zen.sinks import on_import
from .lifecycle import patch


on_import("odoo.http")(patch)
