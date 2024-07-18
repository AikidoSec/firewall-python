"""
SQL Injection algorithm
"""

from aikido_firewall.vulnerabilities.sql_injection.dialects import MySQL
from aikido_firewall.vulnerabilities.sql_injection.query_contains_user_input import (
    query_contains_user_input,
)
from aikido_firewall.vulnerabilities.sql_injection.userinput_contains_sql_syntax import (
    userinput_contains_sqlsyntax,
)
from aikido_firewall.vulnerabilities.sql_injection.uinput_occ_safely_encapsulated import (
    uinput_occ_safely_encapsulated,
)


def detectSQLInjection(query, user_input, dialect):
    if len(user_input) <= 1:
        # We ignore single characters since they are only able to crash the SQL Server,
        # And don't pose a big threat.
        return False

    if len(user_input) > len(query):
        # We ignore cases where the user input is longer than the query.
        # Because the user input can't be part of the query.
        return False

    if not query_contains_user_input(query, user_input):
        # If the user input is not part of the query, return false (No need to check)
        return False

    if userinput_occurrences_safely_encapsulated(query, user_input):
        return False

    # Executing our final check with the massive RegEx
    return userinput_contains_sqlsyntax(user_input, dialect)
