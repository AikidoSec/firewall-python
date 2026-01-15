"""
Sink module for `psycopg`
"""

import aikido_zen.vulnerabilities as vulns
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import patch_function, on_import, before


@before
def _copy(func, instance, args, kwargs):
    statement = get_argument(args, kwargs, 0, "statement")
    op = f"psycopg.{instance.__class__.__name__}.copy"
    register_call(op, "sql_op")

    vulns.run_vulnerability_scan(
        kind="sql_injection", op=op, args=(statement, "postgres")
    )


@before
def _execute(func, instance, args, kwargs):
    query = get_argument(args, kwargs, 0, "query")
    op = f"psycopg.{instance.__class__.__name__}.{func.__name__}"
    vulns.run_vulnerability_scan(kind="sql_injection", op=op, args=(query, "postgres"))


@on_import("psycopg.cursor", "psycopg", version_requirement="3.1.0")
def patch(m):
    """
    patching module psycopg.cursor
    - patches Cursor.copy
    - patches Cursor.execute
    - patches Cursor.executemany
    """
    patch_function(m, "Cursor.copy", _copy)
    patch_function(m, "Cursor.execute", _execute)
    patch_function(m, "Cursor.executemany", _execute)


@on_import("psycopg.cursor_async", "psycopg", version_requirement="3.1.0")
def patch_async(m):
    """
    patching module psycopg.cursor_async (similar to normal patch)
    """
    patch_function(m, "AsyncCursor.copy", _copy)
    patch_function(m, "AsyncCursor.execute", _execute)
    patch_function(m, "AsyncCursor.executemany", _execute)
