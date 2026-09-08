from aikido_zen.context import get_current_context
from aikido_zen.errors import AikidoIDOR
from aikido_zen.helpers.logging import logger
from aikido_zen.ratelimiting.lru_cache import LRUCache
from aikido_zen.thread.thread_cache import get_cache
from aikido_zen.storage.idor_protection_config import idor_protection_store
from .analyze_sql import analyze_sql

_sql_cache = LRUCache(max_items=200, time_to_live_in_ms=600000)


def run_idor_check(query, dialect, query_params=None):
    config = idor_protection_store.get()
    if not config:
        return

    context = get_current_context()
    if not context:
        return

    if context.idor_ignored:
        return

    if not context.tenant_id:
        return

    thread_cache = get_cache()
    if thread_cache and thread_cache.is_bypassed_ip(context.remote_address):
        return

    if not isinstance(query, str):
        return

    cache_key = query + ":" + dialect
    statements = _sql_cache.get(cache_key)
    if statements is None:
        statements = analyze_sql(query, dialect)
        if statements is not None:
            _sql_cache.set(cache_key, statements)

    if not statements:
        return

    # Rust returns {"error": ...} for queries it cannot parse (e.g. %s placeholders)
    if isinstance(statements, dict) and "error" in statements:
        logger.debug("IDOR analyze_sql error: %s", statements["error"])
        return

    if not isinstance(statements, list):
        return

    tenant_column = config.tenant_column_name
    excluded = config.excluded_tables

    for stmt in statements:
        if stmt.get("kind") == "insert":
            _check_insert(
                stmt, tenant_column, excluded, context.tenant_id, query_params
            )
        else:
            _check_where_filters(
                stmt, tenant_column, excluded, context.tenant_id, query_params
            )


def _check_where_filters(stmt, tenant_column, excluded, tenant_id, query_params):
    tables = stmt.get("tables", [])
    filters = stmt.get("filters", [])

    for table_info in tables:
        table_name = table_info.get("name", "")
        if table_name in excluded:
            continue

        matching_filter = _find_tenant_filter(
            filters, tenant_column, table_name, len(tables) == 1
        )

        if matching_filter is None:
            raise AikidoIDOR(
                f"Zen IDOR protection: query on table '{table_name}' "
                f"is missing a filter on column '{tenant_column}'"
            )

        value = _resolve_value(matching_filter, query_params)
        if value is not None and str(value) != tenant_id:
            raise AikidoIDOR(
                f"Zen IDOR protection: query on table '{table_name}' "
                f"filters '{tenant_column}' with value '{value}' "
                f"but tenant ID is '{tenant_id}'"
            )


def _check_insert(stmt, tenant_column, excluded, tenant_id, query_params):
    tables = stmt.get("tables", [])
    rows = stmt.get("insert_columns", [])

    for table_info in tables:
        table_name = table_info.get("name", "")
        if table_name in excluded:
            continue

        for row in rows:
            col_entry = next((e for e in row if e.get("column") == tenant_column), None)

            if col_entry is None:
                raise AikidoIDOR(
                    f"Zen IDOR protection: INSERT on table '{table_name}' "
                    f"is missing column '{tenant_column}'"
                )

            value = _resolve_value(col_entry, query_params)
            if value is not None and str(value) != tenant_id:
                raise AikidoIDOR(
                    f"Zen IDOR protection: INSERT on table '{table_name}' "
                    f"sets '{tenant_column}' to '{value}' "
                    f"but tenant ID is '{tenant_id}'"
                )


def _find_tenant_filter(filters, tenant_column, table_name, single_table):
    for f in filters:
        if f.get("column") != tenant_column:
            continue
        filter_table = f.get("table")
        if filter_table:
            if filter_table == table_name:
                return f
        elif single_table:
            return f
    return None


def _resolve_value(entry, query_params):
    if not entry.get("is_placeholder", False):
        return entry.get("value")

    if not query_params or isinstance(query_params, dict):
        return None

    params = query_params
    if not isinstance(params, (list, tuple)):
        params = list(params) if hasattr(params, "__iter__") else None
        if params is None:
            return None

    # MySQL-style ? placeholder: index is 0-based placeholder_number
    if "placeholder_number" in entry:
        idx = entry["placeholder_number"]
        if isinstance(idx, int) and 0 <= idx < len(params):
            return str(params[idx])
        return None

    # Postgres-style $N placeholder: N is 1-based
    value = entry.get("value", "")
    if isinstance(value, str) and value.startswith("$"):
        try:
            idx = int(value[1:]) - 1
            if 0 <= idx < len(params):
                return str(params[idx])
        except (ValueError, IndexError):
            pass

    return None
