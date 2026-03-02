import sqlite3 as _sqlite3

from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.helpers.modify_arguments import modify_arguments
import aikido_zen.vulnerabilities as vulns
from aikido_zen.helpers.register_call import register_call
from aikido_zen.sinks import (
    patch_function,
    on_import,
    before,
    patch_immutable_class,
)


@before
def _cursor_execute(func, instance, args, kwargs):
    query = get_argument(args, kwargs, 0, "sql")

    register_call("sqlite3.Cursor.execute", "sql_op")
    vulns.run_vulnerability_scan(
        kind="sql_injection", op="sqlite3.Cursor.execute", args=(query, "sqlite")
    )


@before
def _execute(func, instance, args, kwargs):
    op = f"sqlite3.{type(instance).__name__}.{func.__name__}"
    query = get_argument(args, kwargs, 0, "sql")
    register_call(op, "sql_op")
    vulns.run_vulnerability_scan(kind="sql_injection", op=op, args=(query, "sqlite"))


@before
def _executescript(func, instance, args, kwargs):
    op = f"sqlite3.{type(instance).__name__}.{func.__name__}"
    query = get_argument(args, kwargs, 0, "sql_script")
    register_call(op, "sql_op")
    vulns.run_vulnerability_scan(kind="sql_injection", op=op, args=(query, "sqlite"))


def _cursor_patch(func, instance, args, kwargs):
    factory = get_argument(args, kwargs, 0, "factory") or _sqlite3.Cursor
    patched_factory = patch_immutable_class(
        factory,
        {
            "execute": _execute,
            "executemany": _execute,
            "executescript": _executescript,
        },
    )

    new_args, new_kwargs = modify_arguments(args, kwargs, 0, "factory", patched_factory)
    return func(*new_args, **new_kwargs)


def _connect(func, instance, args, kwargs):
    factory = get_argument(args, kwargs, 5, "factory") or _sqlite3.Connection
    connection_patches = {
        "cursor": _cursor_patch
    }

    if _PATCH_CONNECTION_EXECUTE:
        # Since py 3.11 there are more ways than using the cursor to execute (e.g. using the connection)
        connection_patches.update(
            {
                "execute": _execute,
                "executemany": _execute,
                "executescript": _executescript,
            }
        )

    patched_factory = patch_immutable_class(factory, connection_patches)
    new_args, new_kwargs = modify_arguments(args, kwargs, 5, "factory", patched_factory)
    return func(*new_args, **new_kwargs)


@on_import("sqlite3")
def patch(m):
    """
    patches sqlite3, a c library; the "connect" function is not c, after that we use patch_immutable_class to
    patch the factory parameter of the connect function. In this factory we patch the cursor function.
    """
    patch_function(m, "connect", _connect)
