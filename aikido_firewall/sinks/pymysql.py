"""
Sink module for `pymysql`
"""

import copy
import logging
import json
from importlib.metadata import version
import importhook
from aikido_firewall.context import get_current_context
from aikido_firewall.vulnerabilities.sql_injection.context_contains_sql_injection import (
    context_contains_sql_injection,
)
from aikido_firewall.vulnerabilities.sql_injection.dialects import MySQL
from aikido_firewall.background_process import get_comms
from aikido_firewall.errors import AikidoSQLInjection

logger = logging.getLogger("aikido_firewall")


@importhook.on_import("pymysql.connections")
def on_pymysql_import(mysql):
    """
    Hook 'n wrap on `pymysql.connections`
    Our goal is to wrap the query() function of the Connection class :
    https://github.com/PyMySQL/PyMySQL/blob/95635f587ba9076e71a223b113efb08ac34a361d/pymysql/connections.py#L557
    Returns : Modified pymysql.connections object
    """
    modified_mysql = importhook.copy_module(mysql)

    prev_query_function = copy.deepcopy(mysql.Connection.query)

    def aikido_new_query(_self, sql, unbuffered=False):
        logger.debug("Wrapper - `pymysql` version : %s", version("pymysql"))

        context = get_current_context()
        contains_injection = context_contains_sql_injection(
            sql, "pymysql.connections.query", context, MySQL()
        )

        logger.info("sql_injection results : %s", json.dumps(contains_injection))
        if contains_injection:
            get_comms().send_data_to_bg_process("ATTACK", (contains_injection, context))
            should_block_res = get_comms().send_data_to_bg_process(
                action="READ_PROPERTY", obj="block", receive=True
            )
            if should_block_res["success"] and should_block_res["data"]:
                raise AikidoSQLInjection("SQL Injection [aikido_firewall]")

        return prev_query_function(_self, sql, unbuffered=False)

    # pylint: disable=no-member
    setattr(mysql.Connection, "query", aikido_new_query)
    logger.debug("Wrapped `pymysql` module")
    return modified_mysql
