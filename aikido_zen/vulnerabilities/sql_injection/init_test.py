import os
import pytest
from aikido_zen.vulnerabilities.sql_injection import (
    detect_sql_injection,
    should_return_early,
)

"""Removed tests :
-> `I'm writting you` : Invalid SQL
-> Moved a lot of the keywords/words together collection to BAD_SQL_COMMANDS.
-> Removed the following GOOD_SQL_COMMANDS : "abcdefghijklmnop@hotmail.com", "steve@yahoo.com"
    Reason : This should never occur unencapsulated in query, results in 5 tokens or so being morphed into one.
"""
BAD_SQL_COMMANDS = [
    "Roses are red insErt are blue",
    "Roses are red cREATE are blue",
    "Roses are red drop are blue",
    "Roses are red updatE are blue",
    "Roses are red SELECT are blue",
    "Roses are red dataBASE are blue",
    "Roses are red alter are blue",
    "Roses are red grant are blue",
    "Roses are red savepoint are blue",
    "Roses are red commit are blue",
    "Roses are red or blue",
    "Roses are red and lovely",
    "This is a group_concat_test",
    "Termin;ate",
    "Roses <> violets",
    "Roses < Violets",
    "Roses > Violets",
    "Roses != Violets",
    "Roses asks red truncates asks blue",
    "Roses asks reddelete asks blue",
    "Roses asks red WHEREis blue",
    "Roses asks red ORis isAND",
    "I was benchmark ing",
    "We were delay ed",
    "I will waitfor you",
]

GOOD_SQL_COMMANDS = [
    "              ",
    "#",
    "'",
]

# Moved ["'union'  is not UNION", "UNION"], to IS_NOT_INJECTION : This is in fact, not an injection.
IS_NOT_INJECTION = [
    ["'UNION 123' UNION \"UNION 123\"", "UNION 123"],
    ["'union'  is not \"UNION\"", "UNION!"],
    ['"UNION;"', "UNION;"],
    ["SELECT * FROM table", "*"],
    ['"COPY/*"', "COPY/*"],
    ["'union'  is not \"UNION--\"", "UNION--"],
    ["'union'  is not UNION", "UNION"],
]

IS_INJECTION = [
    ["UNTER;", "UNTER;"],
]

DIALECTS = [
    "generic",
    "mysql",
    "postgres",
    "sqlite",
]


def is_sql_injection(sql, input, dialect="all"):
    for current in DIALECTS:
        if dialect == "all" or dialect == current:
            result = detect_sql_injection(sql, input, current)
            assert (
                result == True
            ), f"Expected SQL injection for SQL: {sql} and input: {input} in {current} dialect"


def is_not_sql_injection(sql, input, dialect="all"):
    for current in DIALECTS:
        if dialect == "all" or dialect == current:
            result = detect_sql_injection(sql, input, current)
            assert (
                result == False
            ), f"Expected no SQL injection for SQL: {sql} and input: {input} in {current} dialect"


def test_should_return_early():
    # Test cases where the function should return True

    # User input is empty
    assert should_return_early("SELECT * FROM users", "") == True

    # User input is a single character
    assert should_return_early("SELECT * FROM users", "a") == True

    # User input is larger than query
    assert (
        should_return_early("SELECT * FROM users", "SELECT * FROM users WHERE id = 1")
        == True
    )

    # User input not in query
    assert should_return_early("SELECT * FROM users", "DELETE") == True

    # User input is alphanumerical
    assert should_return_early("SELECT * FROM users123", "users123") == True
    assert should_return_early("SELECT * FROM users_123", "users_123") == True
    assert should_return_early("SELECT __1 FROM users_123", "__1") == True
    assert (
        should_return_early(
            "SELECT * FROM table_name_is_fun_12", "table_name_is_fun_12"
        )
        == True
    )

    # User input is a valid comma-separated number list
    assert should_return_early("SELECT * FROM users", "1,2,3") == True

    # User input is a valid number
    assert should_return_early("SELECT * FROM users", "123") == True

    # User input is a valid number with spaces
    assert should_return_early("SELECT * FROM users", "  123  ") == True

    # User input is a valid number with commas
    assert should_return_early("SELECT * FROM users", "1, 2, 3") == True

    # Test cases where the function should return False

    # User input is in query
    assert should_return_early("SELECT * FROM users", " users") == False

    # User input is a valid string in query
    assert should_return_early("SELECT * FROM users", "SELECT ") == False

    # User input is a valid string in query with special characters
    assert (
        should_return_early("SELECT * FROM users; DROP TABLE", "users; DROP TABLE")
        == False
    )


def test_bad_sql_commands():
    for sql in BAD_SQL_COMMANDS:
        is_sql_injection(sql, sql)


def test_good_sql_commands():
    for sql in GOOD_SQL_COMMANDS:
        is_not_sql_injection(sql, sql)


def test_is_injection():
    for sql, input in IS_INJECTION:
        is_sql_injection(sql, input)


def test_is_not_injection():
    for sql, input in IS_NOT_INJECTION:
        is_not_sql_injection(sql, input)


"""
Moved :
is_sql_injection("SELECT * FROM users WHERE id = 'users\\'", "users\\")
is_sql_injection("SELECT * FROM users WHERE id = 'users\\\\'", "users\\\\")
to is_not_sql_injection. Reason : Invalid SQL.
"""


def test_allow_escape_sequences():
    # Invalid queries :
    is_not_sql_injection("SELECT * FROM users WHERE id = 'users\\'", "users\\")

    is_not_sql_injection("SELECT * FROM users WHERE id = 'users\\\\'", "users\\\\")
    is_not_sql_injection("SELECT * FROM users WHERE id = '\nusers'", "\nusers")
    is_not_sql_injection("SELECT * FROM users WHERE id = '\rusers'", "\rusers")
    is_not_sql_injection("SELECT * FROM users WHERE id = '\tusers'", "\tusers")


# Marked "SELECT * FROM users WHERE id IN ('123')", "'123'" as not a sql injection, Reason :
# We replace '123' token with another token and the token count remains the same. This is also
# Not an actual SQL Injection so the algorithm is valid in it's reasoning.
def test_user_input_inside_in():
    is_not_sql_injection("SELECT * FROM users WHERE id IN ('123')", "'123'")
    is_not_sql_injection("SELECT * FROM users WHERE id IN (123)", "123")
    is_not_sql_injection("SELECT * FROM users WHERE id IN (123, 456)", "123")
    is_not_sql_injection("SELECT * FROM users WHERE id IN (123, 456)", "456")
    is_not_sql_injection("SELECT * FROM users WHERE id IN ('123')", "123")
    is_not_sql_injection("SELECT * FROM users WHERE id IN (13,14,15)", "13,14,15")
    is_not_sql_injection("SELECT * FROM users WHERE id IN (13, 14, 154)", "13, 14, 154")
    is_sql_injection(
        "SELECT * FROM users WHERE id IN (13, 14, 154) OR (1=1)", "13, 14, 154) OR (1=1"
    )


# Updated tests so the strings terminate and this is valid SQL.
def test_check_string_safely_escaped():
    is_sql_injection(
        'SELECT * FROM comments WHERE comment = "I" "m writting you"',
        'I" "m writting you',
    )
    is_sql_injection("SELECT * FROM `comm`ents``", "`comm`ents")
    is_not_sql_injection(
        'SELECT * FROM comments WHERE comment = "I\'m writting you"', "I'm writting you"
    )
    is_not_sql_injection(
        "SELECT * FROM comments WHERE comment = 'I\"m writting you'", 'I"m writting you'
    )
    is_not_sql_injection(
        'SELECT * FROM comments WHERE comment = "I`m writting you"', "I`m writting you"
    )
    # Invalid query (strings don't terminate)
    is_not_sql_injection(
        "SELECT * FROM comments WHERE comment = 'I'm writting you'", "I'm writting you"
    )
    # Positive example of same query :
    is_sql_injection(
        "SELECT * FROM comments WHERE comment = 'I'm writting you--'",
        "I'm writting you--",
    )
    is_sql_injection(
        "SELECT * FROM comments WHERE comment = 'I'm writting you''",
        "I'm writting you'",
    )
    # Invalid query in postgres, tests fallback :
    is_sql_injection("SELECT * FROM `comm` ents", "`comm` ents", "postgres")

    # MySQL Specific code :
    is_sql_injection("SELECT * FROM `comm` ents", "`comm` ents", "mysql")
    is_not_sql_injection("SELECT * FROM `comm'ents`", "comm'ents", "mysql")


def test_not_flag_select_queries():
    is_not_sql_injection("SELECT * FROM users WHERE id = 1", "SELECT")


def test_not_flag_escaped_hash():
    is_not_sql_injection("SELECT * FROM hashtags WHERE name = '#hashtag'", "#hashtag")


def test_comment_same_as_user_input():
    is_sql_injection(
        "SELECT * FROM hashtags WHERE name = '-- Query by name' -- Query by name",
        "-- Query by name",
    )


def test_input_occurs_in_comment():
    is_not_sql_injection(
        "SELECT * FROM hashtags WHERE name = 'name' -- Query by name", "name"
    )


def test_user_input_is_multiline():
    is_sql_injection(
        "SELECT * FROM users WHERE id = 'a'\nOR 1=1#'", "a'\nOR 1=1#", "mysql"
    )
    is_sql_injection(
        "SELECT * FROM users WHERE id = 'a'\nOR 1=1#'", "a'\nOR 1=1#", "generic"
    )
    is_not_sql_injection("SELECT * FROM users WHERE id = 'a\nb\nc';", "a\nb\nc")


def test_user_input_is_longer_than_query():
    is_not_sql_injection("SELECT * FROM users", "SELECT * FROM users WHERE id = 'a'")


def test_sqlite_dollar_placeholder():
    is_sql_injection(
        "SELECT * FROM users WHERE id = '1' OR $$ IS NULL -- '",
        "1' OR $$ IS NULL -- ",
        "sqlite",
    )


def test_multiline_queries():
    is_sql_injection(
        """
        SELECT * FROM `users`
        WHERE id = 123
        """,
        "users`",
    )

    is_sql_injection(
        """
        SELECT *
        FROM users
        WHERE id = '1' OR 1=1
        """,
        "1' OR 1=1",
    )

    is_sql_injection(
        """
        SELECT *
        FROM users
        WHERE id = '1' OR 1=1
        AND is_escaped = '1'' OR 1=1'
        """,
        "1' OR 1=1",
    )

    is_sql_injection(
        """
        SELECT *
        FROM users
        WHERE id = '1' OR 1=1
        AND is_escaped = "1' OR 1=1"
        """,
        "1' OR 1=1",
    )

    is_not_sql_injection(
        """
        SELECT * FROM `users`
        WHERE id = 123
        """,
        "123",
    )

    is_not_sql_injection(
        """
        SELECT * FROM `us``ers`
        WHERE id = 123
        """,
        "users",
    )

    is_not_sql_injection(
        """
        SELECT * FROM users
        WHERE id = 123
        """,
        "123",
    )

    is_not_sql_injection(
        """
        SELECT * FROM users
        WHERE id = '123'
        """,
        "123",
    )

    is_not_sql_injection(
        """
        SELECT *
        FROM users
        WHERE is_escaped = "1' OR 1=1"
        """,
        "1' OR 1=1",
    )


def test_lowercased_input_sql_injection():
    sql = """
        SELECT id,
               email,
               password_hash,
               registered_at,
               is_confirmed,
               first_name,
               last_name
        FROM users WHERE email_lowercase = '' or 1=1 -- a'
    """
    expected_sql_injection = "' OR 1=1 -- a"

    is_sql_injection(sql, expected_sql_injection)


# Removed dangerous character parametized loop : This was all producing invalid SQL.

"""
Marked the following as SQL injection since this would result in 2 or more tokens becoming one :
is_not_sql_injection("foobar)", "foobar)")
is_not_sql_injection("foobar      )", "foobar      )")
is_not_sql_injection("€foobar()", "€foobar()")
"""


def test_function_calls_as_sql_injections():
    is_sql_injection("foobar()", "foobar()")
    is_sql_injection("foobar(1234567)", "foobar(1234567)")
    is_sql_injection("foobar       ()", "foobar       ()")
    is_sql_injection(".foobar()", ".foobar()")
    is_sql_injection("20+foobar()", "20+foobar()")
    is_sql_injection("20-foobar(", "20-foobar(")
    is_sql_injection("20<foobar()", "20<foobar()")
    is_sql_injection("20*foobar  ()", "20*foobar  ()")
    is_sql_injection("!foobar()", "!foobar()")
    is_sql_injection("=foobar()", "=foobar()")
    is_sql_injection("1foobar()", "1foobar()")
    is_sql_injection("1foo_bar()", "1foo_bar()")
    is_sql_injection("1foo-bar()", "1foo-bar()")
    is_sql_injection("#foobar()", "#foobar()")
    is_sql_injection("foobar)", "foobar)")
    is_sql_injection("foobar      )", "foobar      )")
    is_sql_injection("€foobar()", "€foobar()")


def file_paths():
    script_dir = os.path.dirname(__file__)
    return [
        # Taken from https://github.com/payloadbox/sql-injection-payload-list/tree/master
        os.path.join(script_dir, "payloads/Auth_Bypass.txt"),
        os.path.join(script_dir, "payloads/postgres.txt"),
        os.path.join(script_dir, "payloads/mysql.txt"),
        os.path.join(script_dir, "payloads/mssql_and_db2.txt"),
    ]


# Define the Pytest tests
for file_path in file_paths():
    import MySQLdb

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            sql = line.rstrip("\n")
            escaped_sql = MySQLdb._mysql.escape_string(sql).decode("utf-8")

            def test_sql_injection():
                is_sql_injection(sql, sql)
                is_not_sql_injection(f"'{escaped_sql}'", escaped_sql, "mysql")
                is_not_sql_injection(f"'{escaped_sql}'", sql, "mysql")

            def test_sql_injection_query():
                is_sql_injection(f"SELECT * FROM users WHERE id = {sql}", sql)
                is_not_sql_injection(
                    f"SELECT * FROM users WHERE id = '{escaped_sql}'",
                    escaped_sql,
                    "mysql",
                )
                is_not_sql_injection(
                    f"SELECT * FROM users WHERE id = '{escaped_sql}'", sql, "mysql"
                )
