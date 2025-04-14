"""
Sink module for `asyncpg`
"""

from wrapt import when_imported
from aikido_zen.background_process.packages import is_package_compatible
import aikido_zen.vulnerabilities as vulns
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import try_wrap_function_wrapper

REQUIRED_ASYNCPG_VERSION = "0.27.0"


@when_imported("asyncpg.connection")
def patch(m):
    """
    patching module asyncpg.connection
    - patches Connection.execute, Connection.executemany, Connection._execute
    - doesn't patch Cursor class -> are only used to fetch data.
    - doesn't patch Pool class -> uses Connection class
    src: https://github.com/MagicStack/asyncpg/blob/85d7eed40637e7cad73a44ed2439ffeb2a8dc1c2/asyncpg/connection.py#L43
    """
    if not is_package_compatible("asyncpg", REQUIRED_ASYNCPG_VERSION):
        return

    try_wrap_function_wrapper(m, "Connection.execute", _execute)
    try_wrap_function_wrapper(m, "Connection.executemany", _execute)
    try_wrap_function_wrapper(m, "Connection._execute", _execute)


def _execute(func, instance, args, kwargs):
    query = get_argument(args, kwargs, 0, "query")

    op = f"asyncpg.connection.Connection.{func.__name__}"
    vulns.run_vulnerability_scan(kind="sql_injection", op=op, args=(query, "postgres"))

    return func(*args, **kwargs)
