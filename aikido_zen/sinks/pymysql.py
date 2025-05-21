"""
Sink module for `pymysql`
"""

import aikido_zen.vulnerabilities as vulns
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import patch_function, on_import, before


@before
def _execute(func, instance, args, kwargs):
    query = get_argument(args, kwargs, 0, "query")
    if isinstance(query, bytearray):
        # If query is type bytearray, it will be picked up by our wrapping of executemany
        return

    vulns.run_vulnerability_scan(
        kind="sql_injection", op="pymysql.Cursor.execute", args=(query, "mysql")
    )


@before
def _executemany(func, instance, args, kwargs):
    query = get_argument(args, kwargs, 0, "query")

    vulns.run_vulnerability_scan(
        kind="sql_injection", op="pymysql.Cursor.executemany", args=(query, "mysql")
    )


@on_import("pymysql.cursors", "pymysql", version_requirement="0.9.0")
def patch(m):
    """
    patching `pymysql.cursors`
    - patches Cursor.execute(query)
    - patches Cursor.executemany(query)
    https://github.com/PyMySQL/PyMySQL/blob/95635f587ba9076e71a223b113efb08ac34a361d/pymysql/cursors.py#L133
    """
    patch_function(m, "Cursor.execute", _execute)
    patch_function(m, "Cursor.executemany", _executemany)
