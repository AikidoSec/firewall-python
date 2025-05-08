"""
Sink module for `psycopg2`
"""

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
def _connect(func, instance, _args, _kwargs, rv):
    """
    the return value (rv) is the new connection object, we'll change the cursor_factory attribute here.
    """
    if rv.cursor_factory is None:
        # set default if not set
        import psycopg2.extensions

        rv.cursor_factory = psycopg2.extensions.cursor

    rv.cursor_factory = type(
        "AikidoPsycopg2Cursor",
        (rv.cursor_factory,),
        {
            # Allows us to modify these otherwise immutable functions
            "execute": rv.cursor_factory.execute,
            "executemany": rv.cursor_factory.executemany,
        },
    )
    patch_function(rv.cursor_factory, "execute", psycopg2_patch)
    patch_function(rv.cursor_factory, "executemany", psycopg2_patch)


@before
def psycopg2_patch(func, instance, args, kwargs):
    query = get_argument(args, kwargs, 0, "query")
    op = f"psycopg2.Connection.Cursor.{func.__name__}"
    vulns.run_vulnerability_scan(kind="sql_injection", op=op, args=(query, "postgres"))
