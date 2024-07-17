"""
Sink module for `pymysql`
"""

import copy
import logging
from importlib.metadata import version
import importhook

logger = logging.getLogger("aikido_firewall")


@importhook.on_import("pymysql.connections")
def on_flask_import(mysql):
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
        logger.debug("Sql : %s", sql)
        return prev_query_function(_self, sql, unbuffered=False)

    # pylint: disable=no-member
    setattr(mysql.Connection, "query", aikido_new_query)
    logger.debug("Wrapped `pymysql` module")
    return modified_mysql
