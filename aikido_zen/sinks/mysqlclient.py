"""
Sink module for `mysqlclient`
"""

from aikido_zen.helpers.get_argument import get_argument
import aikido_zen.vulnerabilities as vulns
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import patch_function, on_import, before


@before
def _execute(func, instance, args, kwargs):
    query = get_argument(args, kwargs, 0, "query")
    if isinstance(query, bytearray):
        # If query is type bytearray, it will be picked up by our wrapping of executemany
        return

    register_call("MySQLdb.Cursor.execute", "sql_op")
    vulns.run_vulnerability_scan(
        kind="sql_injection", op="MySQLdb.Cursor.execute", args=(query, "mysql")
    )


@before
def _executemany(func, instance, args, kwargs):
    query = get_argument(args, kwargs, 0, "query")

    register_call("MySQLdb.Cursor.executemany", "sql_op")
    vulns.run_vulnerability_scan(
        kind="sql_injection", op="MySQLdb.Cursor.executemany", args=(query, "mysql")
    )


@on_import("MySQLdb.cursors", "mysqlclient", version_requirement="1.5.0")
def patch(m):
    """
    patching MySQLdb.cursors (mysqlclient)
    - patches Cursor.execute(query, ...)
    - patches Cursor.executemany(query, ...)
    """
    patch_function(m, "Cursor.execute", _execute)
    patch_function(m, "Cursor.executemany", _executemany)
