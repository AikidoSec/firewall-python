"""
Sink module for `asyncpg`
"""

import aikido_zen.vulnerabilities as vulns
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import patch_function, before, on_import


@on_import("asyncpg.connection", "asyncpg", version_requirement="0.27.0")
def patch(m):
    """
    patching module asyncpg.connection
    - patches Connection.execute, Connection.executemany, Connection._execute
    - doesn't patch Cursor class -> are only used to fetch data.
    - doesn't patch Pool class -> uses Connection class
    src: https://github.com/MagicStack/asyncpg/blob/85d7eed40637e7cad73a44ed2439ffeb2a8dc1c2/asyncpg/connection.py#L43
    """
    patch_function(m, "Connection.execute", _execute)
    patch_function(m, "Connection.executemany", _execute)
    patch_function(m, "Connection._execute", _execute)


@before
def _execute(func, instance, args, kwargs):
    query = get_argument(args, kwargs, 0, "query")

    op = f"asyncpg.connection.Connection.{func.__name__}"
    vulns.run_vulnerability_scan(kind="sql_injection", op=op, args=(query, "postgres"))
