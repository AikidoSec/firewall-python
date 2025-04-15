"""
Sink module for `psycopg2`
"""

from aikido_zen import logger
from aikido_zen.background_process.packages import is_package_compatible
import aikido_zen.vulnerabilities as vulns
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import on_import, before, patch_function, after


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


@after
def _connect(func, instance, args, kwargs, rv):
    """
    the return value (rv) is the new connection object, we'll change the cursor_factory attribute here.
    """
    # Create new default cursor factory if not exists
    if rv.cursor_factory is None:
        import psycopg2.extensions

        class AikidoDefaultCursor(psycopg2.extensions.cursor):
            pass

        rv.cursor_factory = AikidoDefaultCursor

    patch_function(rv.cursor_factory, "execute", _execute)
    patch_function(rv.cursor_factory, "executemany", _execute)


@before
def _execute(func, instance, args, kwargs):
    query = get_argument(args, kwargs, 0, "query")
    op = f"psycopg2.Connection.Cursor.{func.__name__}"
    vulns.run_vulnerability_scan(kind="sql_injection", op=op, args=(query, "postgres"))
