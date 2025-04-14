"""
Sink module for `mysqlclient`
"""

from wrapt import when_imported

from aikido_zen.background_process.packages import is_package_compatible
from aikido_zen.helpers.get_argument import get_argument
import aikido_zen.vulnerabilities as vulns
from aikido_zen.sinks import try_wrap_function_wrapper

REQUIRED_MYSQLCLIENT_VERSION = "1.5.0"


@when_imported("MySQLdb.cursors")
def patch(m):
    """
    patching MySQLdb.cursors (mysqlclient)
    - patches Cursor.execute(query, ...)
    - patches Cursor.executemany(query, ...)
    """
    if not is_package_compatible("mysqlclient", REQUIRED_MYSQLCLIENT_VERSION):
        return

    try_wrap_function_wrapper(m, "Cursor.execute", _execute)
    try_wrap_function_wrapper(m, "Cursor.executemany", _executemany)


def _execute(func, instance, args, kwargs):
    query = get_argument(args, kwargs, 0, "query")
    if isinstance(query, bytearray):
        # If query is type bytearray, it will be picked up by our wrapping of executemany
        return func(*args, **kwargs)

    vulns.run_vulnerability_scan(
        kind="sql_injection", op="MySQLdb.Cursor.execute", args=(query, "mysql")
    )

    return func(*args, **kwargs)


def _executemany(func, instance, args, kwargs):
    query = get_argument(args, kwargs, 0, "query")

    vulns.run_vulnerability_scan(
        kind="sql_injection", op="MySQLdb.Cursor.executemany", args=(query, "mysql")
    )

    return func(*args, **kwargs)
