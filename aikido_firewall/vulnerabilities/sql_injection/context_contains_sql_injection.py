"""
This will check the context of the request for SQL Injections
"""

import json
from aikido_firewall.helpers.extract_strings_from_user_input import (
    extract_strings_from_user_input,
)
from aikido_firewall.vulnerabilities.sql_injection import detect_sql_injection
from aikido_firewall.helpers.logging import logger
from aikido_firewall.context import UINPUT_SOURCES as SOURCES


def context_contains_sql_injection(sql, operation, context, dialect):
    """
    This will check the context of the request for SQL Injections
    """
    for source in SOURCES:
        logger.debug("Checking source %s for SQL Injection", source)
        if hasattr(context, source):
            user_inputs = extract_strings_from_user_input(getattr(context, source))
            for user_input, path in user_inputs.items():
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
