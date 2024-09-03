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


@importhook.on_import("pymysql.cursors")
def on_pymysql_import(mysql):
    """
    Hook 'n wrap on `pymysql.cursors`
    Our goal is to wrap execute() and executemany() on Cursor class
    https://github.com/PyMySQL/PyMySQL/blob/95635f587ba9076e71a223b113efb08ac34a361d/pymysql/cursors.py#L133
    Returns : Modified pymysql.cursors object
    """
    modified_mysql = importhook.copy_module(mysql)

    prev_execute_func = copy.deepcopy(mysql.Cursor.execute)
    prev_executemany_func = copy.deepcopy(mysql.Cursor.executemany)

    def aikido_new_execute(self, query, args=None):
        if isinstance(query, bytearray):
            logger.debug("Query is bytearray, normally comes from executemany.")
            return prev_execute_func(self, query, args)
        vulns.run_vulnerability_scan(
            kind="sql_injection", op="pymysql.Cursor.execute", args=(query, MySQL())
        )
        return prev_execute_func(self, query, args)

    def aikido_new_executemany(self, query, args):
        op = "pymysql.Cursor.executemany"
        vulns.run_vulnerability_scan(kind="sql_injection", op=op, args=(query, MySQL()))
        return prev_executemany_func(self, query, args)

    setattr(mysql.Cursor, "execute", aikido_new_execute)
    setattr(mysql.Cursor, "executemany", aikido_new_executemany)

    add_wrapped_package("pymysql")
    return modified_mysql
