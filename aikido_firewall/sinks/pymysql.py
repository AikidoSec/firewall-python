"""
Sink module for `pymysql`
"""

import copy
import logging
import importhook
from aikido_firewall.vulnerabilities.sql_injection.dialects import MySQL
from aikido_firewall.background_process.packages import add_wrapped_package
import aikido_firewall.vulnerabilities as vulns

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
        if isinstance(sql, bytearray):
            # executemany() gives a bytearray, convert to string.
            sql = sql.decode("utf-8")
        vulns.run_vulnerability_scan(
            kind="sql_injection", op="pymysql.connections.query", args=(sql, MySQL())
        )

        return prev_query_function(_self, sql, unbuffered=False)

    # pylint: disable=no-member
    setattr(mysql.Connection, "query", aikido_new_query)
    add_wrapped_package("pymysql")
    return modified_mysql
