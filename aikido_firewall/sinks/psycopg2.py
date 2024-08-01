"""
Sink module for `psycopg2`
"""

import copy
from importlib.metadata import version
import importhook
import json
from aikido_firewall.helpers.logging import logger
from aikido_firewall.context import get_current_context
from aikido_firewall.vulnerabilities.sql_injection.context_contains_sql_injection import (
    context_contains_sql_injection,
)
from aikido_firewall.vulnerabilities.sql_injection.dialects import Postgres
from aikido_firewall.background_process import get_comms


@importhook.on_import("psycopg2._psycopg")
def on_psycopg2_import(psycopg2):
    """
    Hook 'n wrap on `psycopg2._psycopg`
    Our goal is to wrap the query() function of the Cursor class :
    https://github.com/PyMySQL/PyMySQL/blob/95635f587ba9076e71a223b113efb08ac34a361d/pymysql/connections.py#L557
    Returns : Modified psycopg2._psycopg object
    """
    modified_psycopg2 = importhook.copy_module(psycopg2)
    prev_connection_init = copy.deepcopy(psycopg2.connection.__init__)
    class AikidoConnection(psycopg2.connection.__class__):
        def __init__(self, *args, **kwargs):
            logger.error("HELKLOOOOO")
            prev_connection_init(self, *args, **kwargs)
        def cursor(self, *args, **kwargs):
            logger.error("CURSWSOORR")
            return generate_aikido_cursor_class(
                prev_query_function=copy.deepcopy(psycopg2.cursor.query),
                prev_cursor_class=psycopg2.cursor
            )

    # pylint: disable=no-member
    setattr(psycopg2, "connection", AikidoConnection)
    setattr(modified_psycopg2, "connection", AikidoConnection)
    logger.debug("Wrapped `psycopg2` module")
    return modified_psycopg2

def generate_aikido_cursor_class(prev_query_function, prev_cursor_class):
    class AikidoCursor(prev_cursor_class):
        def query(self, sql):
            logger.debug("Wrapper - `psycopg2` version : %s", version("pymysql"))
            logger.debug("Sql : %s", sql)

            context = get_current_context()
            contains_injection = context_contains_sql_injection(
                sql, "psycopg2._psycopg.cursor.query", context, Postgres()
            )

            logger.info("sql_injection results : %s", json.dumps(contains_injection))
            if contains_injection:
                get_comms().send_data_to_bg_process("ATTACK", (contains_injection, context))
                should_block = get_comms().poll_config("block")
                if should_block:
                    raise Exception("SQL Injection [aikido_firewall]")

            return prev_query_function(self, sql, unbuffered=False)
    return AikidoCursor
