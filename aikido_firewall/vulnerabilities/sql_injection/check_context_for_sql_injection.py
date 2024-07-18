"""
This will check the context of the request for SQL Injections
"""

from aikido_firewall.helpers.extract_strings_from_user_input import (
    extract_strings_from_user_input,
)
from aikido_firewall.vulnerabilities.sql_injection import detect_sql_injection

SOURCES = ["STILL_NEED_TO_DO_SOMETHING_HERE"]


def check_context_for_sql_injection(sql, operation, context, dialect):
    """
    This will check the context of the request for SQL Injections
    """
    for source in SOURCES:
        if context.data.get(source):
            user_inputs = extract_strings_from_user_input(context.data[source])
            for user_input in user_inputs:
                if detect_sql_injection(sql, user_input, dialect):
                    return {
                        "operation": operation,
                        "kind": "sql_injection",
                        "source": source,
                        "pathToPayload": "path",  # Placeholder for path information
                        "metadata": {},
                        "payload": user_input,
                    }
