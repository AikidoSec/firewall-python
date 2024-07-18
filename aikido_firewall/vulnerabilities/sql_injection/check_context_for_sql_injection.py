"""
This will check the context of the request for SQL Injections
"""

from aikido_firewall.helpers.extract_strings_from_user_input import (
    extract_strings_from_user_input,
)
from aikido_firewall.vulnerabilities.sql_injection import detect_sql_injection
from aikido_firewall.helpers.logging import logger

SOURCES = ["body"]


def check_context_for_sql_injection(sql, operation, context, dialect):
    """
    This will check the context of the request for SQL Injections
    """
    for source in SOURCES:
        logger.debug("Checking source %s for SQL Injection", source)
        if hasattr(context, source):
            user_inputs = extract_strings_from_user_input(getattr(context, source))
            logger.debug("User inputs : %s", json.dumps(user_inputs))
            for user_input in user_inputs:
                logger.debug("Checking user input %s", user_input)
                if detect_sql_injection(sql, user_input, dialect):
                    return {
                        "operation": operation,
                        "kind": "sql_injection",
                        "source": source,
                        "pathToPayload": "path",  # Placeholder for path information
                        "metadata": {},
                        "payload": user_input,
                    }
    return {}
