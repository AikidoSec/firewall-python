"""
Sink module for `psycopg2`
"""

from aikido_zen import logger
from aikido_zen.background_process.packages import is_package_compatible
import aikido_zen.vulnerabilities as vulns
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import on_import, before, patch_function


@on_import("psycopg2")
def patch(m):
    """
    patching module psycopg2
    - patches psycopg2.connect
    Warning: cannot set 'execute' attribute of immutable type 'psycopg2.extensions.cursor'
    """
    compatible = is_package_compatible(
        required_version="2.9.2", packages=["psycopg2", "psycopg2-binary"]
    )
    if not compatible:
        # Users can install either psycopg2 or psycopg2-binary, we need to check if at least
        # one is installed and if they meet version requirements
        return

    patch_function(m, "connect", _connect)


def _connect(func, instance, args, kwargs):
    cursor_factory = get_argument(args, kwargs, 2, "cursor_factory")
    if "cursor_factory" in kwargs:
        del kwargs["cursor_factory"]
    try:
        if cursor_factory is None:
            import psycopg2.extensions

            class AikidoDefaultCursor(psycopg2.extensions.cursor):
                pass

            cursor_factory = AikidoDefaultCursor

        # patch execute or executemany of an already existing cursor or of a new one
        patch_function(cursor_factory, "execute", _execute)
        patch_function(cursor_factory, "executemany", _execute)

    except Exception as e:
        logger.info("patch of psycopg2 failed: %s", e.msg)

    return func(*args, cursor_factory=cursor_factory, **kwargs)


@before
def _execute(func, instance, args, kwargs):
    query = get_argument(args, kwargs, 0, "query")
    op = f"psycopg2.Connection.Cursor.{func.__name__}"
    vulns.run_vulnerability_scan(kind="sql_injection", op=op, args=(query, "postgres"))
