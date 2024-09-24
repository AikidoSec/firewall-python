"""
This will check the context of the request for SQL Injections
"""

from aikido_zen.helpers.extract_strings_from_context import extract_strings_from_context
from aikido_zen.vulnerabilities.sql_injection import detect_sql_injection


def context_contains_sql_injection(sql, operation, context, dialect):
    """
    This will check the context of the request for SQL Injections
    """
    if not isinstance(sql, str):
        # Only supports SQL queries that are strings, return otherwise.
        return {}
    for user_input, path, source in extract_strings_from_context(context):
        if detect_sql_injection(sql, user_input, dialect):
            return {
                "operation": operation,
                "kind": "sql_injection",
                "source": source,
                "pathToPayload": path,
                "metadata": {"sql": sql},
                "payload": user_input,
            }
    return {}
