"""
Sink module for `sqlite3`
"""

from aikido_zen.helpers.get_argument import get_argument
import aikido_zen.vulnerabilities as vulns
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import patch_function, on_import, before


@before
def _cursor_execute(func, instance, args, kwargs):
    query = get_argument(args, kwargs, 0, "sql")

    register_call("sqlite3.Cursor.execute", "sql_op")
    vulns.run_vulnerability_scan(
        kind="sql_injection", op="sqlite3.Cursor.execute", args=(query, "sqlite")
    )


@before
def _cursor_executemany(func, instance, args, kwargs):
    query = get_argument(args, kwargs, 0, "sql")

    register_call("sqlite3.Cursor.executemany", "sql_op")
    vulns.run_vulnerability_scan(
        kind="sql_injection", op="sqlite3.Cursor.executemany", args=(query, "sqlite")
    )


@before
def _cursor_executescript(func, instance, args, kwargs):
    query = get_argument(args, kwargs, 0, "sql_script")

    register_call("sqlite3.Cursor.executescript", "sql_op")
    vulns.run_vulnerability_scan(
        kind="sql_injection",
        op="sqlite3.Cursor.executescript",
        args=(query, "sqlite"),
    )


@before
def _connection_execute(func, instance, args, kwargs):
    query = get_argument(args, kwargs, 0, "sql")

    register_call("sqlite3.Connection.execute", "sql_op")
    vulns.run_vulnerability_scan(
        kind="sql_injection", op="sqlite3.Connection.execute", args=(query, "sqlite")
    )


@before
def _connection_executemany(func, instance, args, kwargs):
    query = get_argument(args, kwargs, 0, "sql")

    register_call("sqlite3.Connection.executemany", "sql_op")
    vulns.run_vulnerability_scan(
        kind="sql_injection",
        op="sqlite3.Connection.executemany",
        args=(query, "sqlite"),
    )


@before
def _connection_executescript(func, instance, args, kwargs):
    query = get_argument(args, kwargs, 0, "sql_script")

    register_call("sqlite3.Connection.executescript", "sql_op")
    vulns.run_vulnerability_scan(
        kind="sql_injection",
        op="sqlite3.Connection.executescript",
        args=(query, "sqlite"),
    )


@on_import("sqlite3")
def patch(m):
    """
    patching sqlite3
    - patches Cursor.execute(sql, ...)
    - patches Cursor.executemany(sql, ...)
    - patches Cursor.executescript(sql_script)
    - patches Connection.execute(sql, ...)
    - patches Connection.executemany(sql, ...)
    - patches Connection.executescript(sql_script)
    """
    patch_function(m, "Cursor.execute", _cursor_execute)
    patch_function(m, "Cursor.executemany", _cursor_executemany)
    patch_function(m, "Cursor.executescript", _cursor_executescript)
    patch_function(m, "Connection.execute", _connection_execute)
    patch_function(m, "Connection.executemany", _connection_executemany)
    patch_function(m, "Connection.executescript", _connection_executescript)
