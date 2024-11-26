"""
Sink module for `psycopg2`
"""

import copy
import aikido_zen.importhook as importhook
from aikido_zen.background_process.packages import pkg_compat_check
import aikido_zen.vulnerabilities as vulns

PSYCOPG2_REQUIRED_VERSION = "2.9.2"


def wrap_cursor_factory(cursor_factory):
    former_cursor_factory = copy.deepcopy(cursor_factory)
    import psycopg2.extensions as ext

    class AikidoWrappedCursor(ext.cursor):
        def execute(self, *args, **kwargs):
            """Aikido's wrapped execute function"""
            vulns.run_vulnerability_scan(
                kind="sql_injection",
                op="psycopg2.Connection.Cursor.execute",
                args=(args[0], "postgres"),  #  args[0] : sql
            )
            if former_cursor_factory and hasattr(former_cursor_factory, "execute"):
                return former_cursor_factory.execute(self, *args, **kwargs)
            return ext.cursor.execute(self, *args, **kwargs)

        def executemany(self, *args, **kwargs):
            """Aikido's wrapped executemany function"""
            sql = args[0]  # The data is double, but sql only once.
            vulns.run_vulnerability_scan(
                kind="sql_injection",
                op="psycopg2.Connection.Cursor.executemany",
                args=(sql, "postgres"),
            )
            if former_cursor_factory and hasattr(former_cursor_factory, "executemany"):
                return former_cursor_factory.executemany(self, *args, **kwargs)
            return ext.cursor.executemany(self, *args, **kwargs)

    return AikidoWrappedCursor


@importhook.on_import("psycopg2")
def on_psycopg2_import(psycopg2):
    """
    Hook 'n wrap on `psycopg2.connect` function, we modify the cursor_factory
    of the result of this connect function.
    """
    # Users can install either psycopg2 or psycopg2-binary, we need to check if at least
    # one is installed and if they meet version requirements :
    if not pkg_compat_check(
        "psycopg2", PSYCOPG2_REQUIRED_VERSION
    ) and not pkg_compat_check("psycopg2-binary", PSYCOPG2_REQUIRED_VERSION):
        # Both pyscopg2 and psycopg2-binary are not supported, abort wrapping
        return psycopg2
    modified_psycopg2 = importhook.copy_module(psycopg2)
    former_connect_function = copy.deepcopy(psycopg2.connect)

    def aikido_connect(*args, **kwargs):
        former_conn = former_connect_function(*args, **kwargs)
        former_conn.cursor_factory = wrap_cursor_factory(former_conn.cursor_factory)
        return former_conn

    # pylint: disable=no-member
    setattr(psycopg2, "connect", aikido_connect)
    setattr(modified_psycopg2, "connect", aikido_connect)
    return modified_psycopg2
