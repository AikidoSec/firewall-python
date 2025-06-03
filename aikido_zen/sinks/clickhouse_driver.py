from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.sinks import before, on_import, patch_function
from aikido_zen.vulnerabilities import run_vulnerability_scan


@before
def _execute(func, instance, args, kwargs):
    kind = "sql_injection"
    op = "clickhouse_driver.Client.execute"
    query = get_argument(args, kwargs, 0, "query")
    run_vulnerability_scan(kind, op, args=(query, "clickhouse"))


@on_import("clickhouse_driver", package="clickhouse_driver")
def patch(m):
    """
    patching module clickhouse_driver
    - patches clickhouse_driver.Client.execute
    - patches clickhouse_driver.Client.execute_iter
    - patches clickhouse_driver.Client.execute_with_progress
    """
    patch_function(m, "Client.execute", _execute)
    patch_function(m, "Client.execute_iter", _execute)
    patch_function(m, "Client.execute_with_progress", _execute)
