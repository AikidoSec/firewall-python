"""
Sink module for `psycopg2`
"""

import copy
import importhook
from aikido_firewall.vulnerabilities.sql_injection.dialects import Postgres
from aikido_firewall.background_process.packages import add_wrapped_package
import aikido_firewall.vulnerabilities as vulns


def wrap_cursor_factory(cursor_factory):
    former_cursor_factory = copy.deepcopy(cursor_factory)
    import psycopg2.extensions as ext

    class AikidoWrappedCursor(ext.cursor):
        def execute(self, *args, **kwargs):
            """Aikido's wrapped execute function"""
            vulns.run_vulnerability_scan(
                kind="sql_injection",
                op="psycopg2.Connection.Cursor.execute",
                args=(args[0], Postgres()),  #  args[0] : sql
            )
            if former_cursor_factory and hasattr(former_cursor_factory, "execute"):
                return former_cursor_factory.execute(self, *args, **kwargs)
            return super().execute(*args, **kwargs)

        def executemany(self, *args, **kwargs):
            """Aikido's wrapped executemany function"""
            sql = args[0]  # The data is double, but sql only once.
            vulns.run_vulnerability_scan(
                kind="sql_injection",
                op="psycopg2.Connection.Cursor.executemany",
                args=(sql, Postgres()),
            )
            if former_cursor_factory and hasattr(former_cursor_factory, "executemany"):
                return former_cursor_factory.executemany(self, *args, **kwargs)
            return super().executemany(*args, **kwargs)

    return AikidoWrappedCursor


@importhook.on_import("psycopg2")
def on_psycopg2_import(psycopg2):
    """
    Hook 'n wrap on `psycopg2.connect` function, we modify the cursor_factory
    of the result of this connect function.
    """
    modified_psycopg2 = importhook.copy_module(psycopg2)
    former_connect_function = copy.deepcopy(psycopg2.connect)

    def aikido_connect(*args, **kwargs):
        former_conn = former_connect_function(*args, **kwargs)
        former_conn.cursor_factory = wrap_cursor_factory(former_conn.cursor_factory)
        return former_conn

    # pylint: disable=no-member
    setattr(psycopg2, "connect", aikido_connect)
    setattr(modified_psycopg2, "connect", aikido_connect)
    add_wrapped_package("psycopg2")
    add_wrapped_package("psycopg2-binary")
    return modified_psycopg2
