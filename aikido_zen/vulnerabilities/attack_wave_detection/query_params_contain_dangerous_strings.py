from aikido_zen.context import Context
from aikido_zen.helpers.extract_strings_from_user_input import (
    extract_strings_from_user_input_cached,
)

keywords = {
    "SELECT (CASE WHEN",
    "SELECT COUNT(",
    "SLEEP(",
    "WAITFOR DELAY",
    "SELECT LIKE(CHAR(",
    "INFORMATION_SCHEMA.COLUMNS",
    "INFORMATION_SCHEMA.TABLES",
    "MD5(",
    "DBMS_PIPE.RECEIVE_MESSAGE",
    "SYSIBM.SYSTABLES",
    "RANDOMBLOB(",
    "SELECT * FROM",
    "1'='1",
    "PG_SLEEP(",
    "UNION ALL SELECT",
    "../",
}


def query_params_contain_dangerous_payload(context: Context) -> bool:
    """
    Check the query for some common SQL or path traversal patterns.
    """
    if not context.query:
        return False

    for s in extract_strings_from_user_input_cached(context.query, "query"):
        # Performance optimization
        if len(s) < 5 or len(s) > 1000:
            continue
        for keyword in keywords:
            if keyword.upper() in s.upper():
                return True
    return False
