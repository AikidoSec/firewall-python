"""
Sink module for `mysqlclient`
"""

import copy
import importhook
from aikido_firewall.vulnerabilities.sql_injection.dialects import MySQL
from aikido_firewall.background_process.packages import add_wrapped_package
from aikido_firewall.helpers.logging import logger
import aikido_firewall.vulnerabilities as vulns


@importhook.on_import("MySQLdb.cursors")
def on_mysqlclient_import(mysql):
    """
    Hook 'n wrap on `MySQLdb.cursors`
    Our goal is to wrap the query() function of the Connection class :
    https://github.com/PyMySQL/mysqlclient/blob/9fd238b9e3105dcbed2b009a916828a38d1f0904/src/MySQLdb/connections.py#L257
    Returns : Modified MySQLdb.connections object
    """
    modified_mysql = importhook.copy_module(mysql)
    prev_execute_func = copy.deepcopy(mysql.Cursor.execute)
    prev_executemany_func = copy.deepcopy(mysql.Cursor.executemany)

    def aikido_new_execute(self, query, args=None):
        if isinstance(query, bytearray):
            logger.debug("Query is bytearray, normally comes from executemany.")
            return prev_execute_func(self, query, args)
        vulns.run_vulnerability_scan(
            kind="sql_injection", op="MySQLdb.Cursor.execute", args=(query, MySQL())
        )
        return prev_execute_func(self, query, args)

    def aikido_new_executemany(self, query, args):
        op = "MySQLdb.Cursor.executemany"
        vulns.run_vulnerability_scan(kind="sql_injection", op=op, args=(query, MySQL()))
        return prev_executemany_func(self, query, args)

    setattr(mysql.Cursor, "execute", aikido_new_execute)
    setattr(mysql.Cursor, "executemany", aikido_new_executemany)
    add_wrapped_package("mysqlclient")
    return modified_mysql
