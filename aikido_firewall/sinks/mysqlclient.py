"""
Sink module for `mysqlclient`
"""

import copy
import json
from importlib.metadata import version
import importhook
from aikido_firewall.context import get_current_context
from aikido_firewall.vulnerabilities.sql_injection.context_contains_sql_injection import (
    context_contains_sql_injection,
)
from aikido_firewall.vulnerabilities.sql_injection.dialects import MySQL
from aikido_firewall.helpers.logging import logger
from aikido_firewall.background_process import get_comms
from aikido_firewall.errors import AikidoSQLInjection


@importhook.on_import("MySQLdb.connections")
def on_mysqlclient_import(mysql):
    """
    Hook 'n wrap on `MySQLdb.connections`
    Our goal is to wrap the query() function of the Connection class :
    https://github.com/PyMySQL/mysqlclient/blob/9fd238b9e3105dcbed2b009a916828a38d1f0904/src/MySQLdb/connections.py#L257
    Returns : Modified MySQLdb.connections object
    """
    modified_mysql = importhook.copy_module(mysql)

    prev_query_function = copy.deepcopy(mysql.Connection.query)

    def aikido_new_query(_self, sql):
        logger.debug("Wrapper - `mysqlclient` version : %s", version("mysqlclient"))

        context = get_current_context()
        contains_injection = context_contains_sql_injection(
            sql.decode("utf-8"), "MySQLdb.connections.query", context, MySQL()
        )

        logger.debug("sql_injection results : %s", json.dumps(contains_injection))
        if contains_injection:
            get_comms().send_data_to_bg_process("ATTACK", (contains_injection, context))
            should_block_res = get_comms().send_data_to_bg_process(
                action="READ_PROPERTY", obj="block", receive=True
            )
            if should_block_res["success"] and should_block_res["data"]:
                raise AikidoSQLInjection("SQL Injection [aikido_firewall]")

        return prev_query_function(_self, sql)

    # pylint: disable=no-member
    setattr(mysql.Connection, "query", aikido_new_query)
    logger.debug("Wrapped `mysqlclient` module")
    return modified_mysql
