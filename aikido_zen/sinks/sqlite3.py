"""
Sink module for `sqlite3`

sqlite3 uses C-level types for Connection and Cursor, so we cannot directly
patch their methods with wrapt. Instead we:
1. Intercept `sqlite3.connect` and inject a custom `factory` parameter.
2. The custom factory is a dynamic Python Connection subclass whose `cursor()`
   returns a wrapped Cursor subclass.
3. All SQL interception happens at the Cursor level. Connection shortcut methods
   (execute, executemany, executescript) internally call cursor methods, so
   wrapping only the Cursor avoids double-counting.
"""

import sqlite3 as _sqlite3

from aikido_zen.helpers.get_argument import get_argument
import aikido_zen.vulnerabilities as vulns
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import patch_function, on_import, before, before_modify_return


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
        kind="sql_injection",
        op="sqlite3.Cursor.executemany",
        args=(query, "sqlite"),
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


def _build_aikido_cursor(base_cursor_cls):
    """
    Creates a Python-level subclass of the given Cursor class with mutable
    method slots so that wrapt can patch them.
    """
    cls = type(
        "AikidoSQLite3Cursor",
        (base_cursor_cls,),
        {
            "execute": base_cursor_cls.execute,
            "executemany": base_cursor_cls.executemany,
            "executescript": base_cursor_cls.executescript,
        },
    )
    patch_function(cls, "execute", _cursor_execute)
    patch_function(cls, "executemany", _cursor_executemany)
    patch_function(cls, "executescript", _cursor_executescript)
    return cls


_AikidoCursor = _build_aikido_cursor(_sqlite3.Cursor)


def _aikido_cursor(self, *args, **kwargs):
    """Replacement cursor() that returns an AikidoSQLite3Cursor instance."""
    return _AikidoCursor(self)


def _build_aikido_connection(base_conn_cls):
    """
    Creates a Python-level Connection subclass whose cursor() returns
    wrapped cursors.
    """
    return type(
        "AikidoSQLite3Connection",
        (base_conn_cls,),
        {
            "cursor": _aikido_cursor,
        },
    )


_AikidoConnection = _build_aikido_connection(_sqlite3.Connection)


@before_modify_return
def _connect(func, instance, args, kwargs):
    """
    Intercept sqlite3.connect to inject our Connection factory.
    The factory parameter is the 6th positional arg (index 5) or a keyword arg.
    """
    # Determine the user-specified factory, if any
    factory = kwargs.get("factory")
    if factory is None and len(args) > 5:
        factory = args[5]
    if factory is None:
        factory = _sqlite3.Connection

    # If the user passed a custom factory, build a new wrapped subclass for it
    if factory is _sqlite3.Connection:
        aikido_factory = _AikidoConnection
    else:
        aikido_factory = _build_aikido_connection(factory)

    # Build new args with our factory injected as a keyword
    new_args = args[:5] if len(args) > 5 else args
    new_kwargs = dict(kwargs)
    new_kwargs["factory"] = aikido_factory

    return func(*new_args, **new_kwargs)


@on_import("sqlite3")
def patch(m):
    """
    patching sqlite3
    - patches sqlite3.connect to inject a wrapped Connection factory
    - wrapped connections produce wrapped cursors
    - Cursor.execute, Cursor.executemany, Cursor.executescript are intercepted
    """
    patch_function(m, "connect", _connect)
