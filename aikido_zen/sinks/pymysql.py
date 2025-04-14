"""
Sink module for `pymysql`
"""

from wrapt import when_imported
from aikido_zen.background_process.packages import is_package_compatible
import aikido_zen.vulnerabilities as vulns
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import try_wrap_function_wrapper

REQUIRED_PYMYSQL_VERSION = "0.9.0"


def _execute(func, instance, args, kwargs):
    query = get_argument(args, kwargs, 0, "query")
    if isinstance(query, bytearray):
        # If query is type bytearray, it will be picked up by our wrapping of executemany
        return func(*args, **kwargs)

    vulns.run_vulnerability_scan(
        kind="sql_injection", op="pymysql.Cursor.execute", args=(query, "mysql")
    )

    return func(*args, **kwargs)


def _executemany(func, instance, args, kwargs):
    query = get_argument(args, kwargs, 0, "query")

    vulns.run_vulnerability_scan(
        kind="sql_injection", op="pymysql.Cursor.executemany", args=(query, "mysql")
    )

    return func(*args, **kwargs)


@when_imported("pymysql.cursors")
def patch(m):
    """
    patching `pymysql.cursors`
    - patches Cursor.execute(query)
    - patches Cursor.executemany(query)
    https://github.com/PyMySQL/PyMySQL/blob/95635f587ba9076e71a223b113efb08ac34a361d/pymysql/cursors.py#L133
    """
    if not is_package_compatible("pymysql", REQUIRED_PYMYSQL_VERSION):
        return

    try_wrap_function_wrapper(m, "Cursor.execute", _execute)
    try_wrap_function_wrapper(m, "Cursor.executemany", _executemany)
