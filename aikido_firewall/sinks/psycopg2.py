"""
Sink module for `psycopg2`
"""

import copy
import importhook
from aikido_firewall.vulnerabilities.sql_injection.dialects import Postgres
from aikido_firewall.background_process.packages import add_wrapped_package
from aikido_firewall.vulnerabilities import run_vulnerability_scan


class MutableAikidoConnection:
    """Aikido's mutable connection class"""

    def __init__(self, former_conn):
        self._former_conn = former_conn
        self._cursor_func_copy = copy.deepcopy(former_conn.cursor)

    def __getattr__(self, name):
        if name != "cursor":
            return getattr(self._former_conn, name)

        # Return a function dynamically
        def cursor(*args, **kwargs):
            former_cursor = self._cursor_func_copy(*args, **kwargs)
            return MutableAikidoCursor(former_cursor)

        return cursor


class MutableAikidoCursor:
    """Aikido's mutable cursor class"""

    def __init__(self, former_cursor):
        self._former_cursor = former_cursor
        self._execute_func_copy = copy.deepcopy(former_cursor.execute)
        self._executemany_func_copy = copy.deepcopy(former_cursor.executemany)

    def __getattr__(self, name):
        if not name in ["execute", "executemany"]:
            return getattr(self._former_cursor, name)

        # Return a function dynamically
        def execute(*args, **kwargs):
            run_vulnerability_scan(
                kind="sql_injection",
                op="pymysql.connection.cursor.execute",
                args=(args[0], Postgres()),  #  args[0] : sql
            )
            return self._execute_func_copy(*args, **kwargs)

        def executemany(*args, **kwargs):
            for sql in args[0]:
                run_vulnerability_scan(
                    kind="sql_injection",
                    op="pymysql.connection.cursor.executemany",
                    args=(sql, Postgres()),
                )
            return self._executemany_func_copy(*args, **kwargs)

        if name == "execute":
            return execute
        return executemany


@importhook.on_import("psycopg2._psycopg")
def on_psycopg2_import(psycopg2):
    """
    Hook 'n wrap on `psycopg2._psycopg._connect` function
    1. We first instantiate a MutableAikidoConnection, because the connection
    class is immutable.
    2. This class has an adapted __getattr__ so that everything redirects to
    the created actual connection, except for "cursor()" function!
    3. When the cursor() function is executed, we instantiate a MutableAikidoCursor
    which is also because the cursor class is immutable
    4. when .execute() is executed on this cursor we can intercept it, the rest
    gets redirected back using __getattr__ to the original cursor
    Returns : Modified psycopg2._psycopg._connect function
    """
    modified_psycopg2 = importhook.copy_module(psycopg2)
    prev__connect_create = copy.deepcopy(psycopg2._connect)

    def aik__connect(*args, **kwargs):
        conn = prev__connect_create(*args, **kwargs)
        return MutableAikidoConnection(conn)

    # pylint: disable=no-member
    setattr(psycopg2, "_connect", aik__connect)
    setattr(modified_psycopg2, "_connect", aik__connect)
    add_wrapped_package("psycopg2")
    add_wrapped_package("psycopg2-binary")
    return modified_psycopg2
