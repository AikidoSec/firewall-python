"""
This will check the context of the request for SQL Injections
"""

import os

from aikido_zen.helpers.extract_strings_from_context import extract_strings_from_context
from aikido_zen.vulnerabilities.sql_injection import detect_sql_injection


def should_block_invalid_sql_queries():
    env_val = os.environ.get("AIKIDO_BLOCK_INVALID_SQL")
    if env_val is None:
        return True
    return env_val.lower() in ["true", "1"]


def context_contains_sql_injection(sql, operation, context, dialect):
    """
    This will check the context of the request for SQL Injections
    """
    if not isinstance(sql, str):
        # Only supports SQL queries that are strings, return otherwise.
        return {}
    for user_input, path, source in extract_strings_from_context(context):
        result = detect_sql_injection(sql, user_input, dialect)

        if result == 1:
            return {
                "operation": operation,
                "kind": "sql_injection",
                "source": source,
                "pathToPayload": path,
                "metadata": {
                    "sql": sql,
                    "dialect": dialect,
                },
                "payload": user_input,
            }

        if result == 3 and should_block_invalid_sql_queries():
            return {
                "operation": operation,
                "kind": "sql_injection",
                "source": source,
                "pathToPayload": path,
                "metadata": {
                    "sql": sql,
                    "dialect": dialect,
                    "failedToTokenize": "true",
                },
                "payload": user_input,
            }
    return {}
