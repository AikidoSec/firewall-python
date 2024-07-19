"""
See function docstring
"""


def query_contains_user_input(query, user_input):
    """
    This function is the first step to determine if an SQL Injection is happening,
    If the sql statement contains user input, this function returns true (case-insensitive)
    @param query The SQL Statement you want to check it against
    @param user_input The user input you want to check
    @returns True when the sql statement contains the input
    """
    lw_query = query.lower()
    lw_input = user_input.lower()
    return lw_input in lw_query
