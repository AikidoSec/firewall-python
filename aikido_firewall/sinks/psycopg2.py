"""
Sink module for `psycopg2`
"""

import copy
import json
import importhook
from aikido_firewall.helpers.logging import logger
from aikido_firewall.context import get_current_context
from aikido_firewall.vulnerabilities.sql_injection.context_contains_sql_injection import (
    context_contains_sql_injection,
)
from aikido_firewall.vulnerabilities.sql_injection.dialects import Postgres
from aikido_firewall.background_process import get_comms


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


def execute_sql_detection_code(sql):
    """
    Executes the sql algorithm : Should block or not, get context, ...
    """
    context = get_current_context()
    contains_injection = context_contains_sql_injection(
        sql, "pymysql.connections.query", context, Postgres()
    )

    logger.info("sql_injection results : %s", json.dumps(contains_injection))
    if contains_injection:
        get_comms().send_data_to_bg_process("ATTACK", (contains_injection, context))
        should_block = get_comms().poll_config("block")
        if should_block:
            raise Exception("SQL Injection [aikido_firewall]")


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
            execute_sql_detection_code(sql=args[0])
            return self._execute_func_copy(*args, **kwargs)

        def executemany(*args, **kwargs):
            for sql in args[0]:
                execute_sql_detection_code(sql)
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
    logger.debug("Wrapped `psycopg2` module")
    return modified_psycopg2
