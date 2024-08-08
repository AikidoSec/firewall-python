"""
Sink module for `mysqlclient`
"""

import copy
import importhook
from aikido_firewall.vulnerabilities.sql_injection.dialects import MySQL
from aikido_firewall.background_process.packages import add_wrapped_package
from aikido_firewall.vulnerabilities import run_vulnerability_scan


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
        run_vulnerability_scan(
            kind="sql_injection",
            op="MySQLdb.connections.query",
            args=(sql.decode("utf-8"), MySQL()),
        )

        return prev_query_function(_self, sql)

    # pylint: disable=no-member
    setattr(mysql.Connection, "query", aikido_new_query)
    add_wrapped_package("MySQLdb")
    return modified_mysql
