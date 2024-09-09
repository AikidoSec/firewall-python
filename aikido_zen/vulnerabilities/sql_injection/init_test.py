import os
import pytest
from aikido_zen.vulnerabilities.sql_injection import detect_sql_injection
from aikido_zen.vulnerabilities.sql_injection.dialects import MySQL
from aikido_zen.vulnerabilities.sql_injection.dialects import Postgres
from aikido_zen.vulnerabilities.sql_injection.consts import SQL_DANGEROUS_IN_STRING

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
    "I'm writting you",
    "Termin;ate",
    "Roses <> violets",
    "Roses < Violets",
    "Roses > Violets",
    "Roses != Violets",
]

GOOD_SQL_COMMANDS = [
    "Roses are red rollbacks are blue",
    "Roses are red truncates are blue",
    "Roses are reddelete are blue",
    "Roses are red WHEREis blue",
    "Roses are red ORis isAND",
    "abcdefghijklmnop@hotmail.com",
    "steve@yahoo.com",
    "I was benchmark ing",
    "We were delay ed",
    "I will waitfor you",
    "#",
    "'",
]

IS_NOT_INJECTION = [
    ["'UNION 123' UNION \"UNION 123\"", "UNION 123"],
    ["'union'  is not \"UNION\"", "UNION!"],
    ['"UNION;"', "UNION;"],
    ["SELECT * FROM table", "*"],
    ['"COPY/*"', "COPY/*"],
    ["'union'  is not \"UNION--\"", "UNION--"],
]

IS_INJECTION = [
    ["'union'  is not UNION", "UNION"],
    ["UNTER;", "UNTER;"],
]


def is_sql_injection(sql, input):
    result = detect_sql_injection(sql, input, MySQL())
    assert result == True, f"Expected SQL injection for SQL: {sql} and input: {input}"
    result = detect_sql_injection(sql, input, Postgres())
    assert result == True, f"Expected SQL injection for SQL: {sql} and input: {input}"
    return result


def is_not_sql_injection(sql, input):
    result = detect_sql_injection(sql, input, MySQL())
    assert (
        result == False
    ), f"Expected no SQL injection for SQL: {sql} and input: {input}"
    result = detect_sql_injection(sql, input, Postgres())
    assert (
        result == False
    ), f"Expected no SQL injection for SQL: {sql} and input: {input}"
    return result


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


def test_allow_escape_sequences():
    is_sql_injection("SELECT * FROM users WHERE id = 'users\\'", "users\\")
    is_sql_injection("SELECT * FROM users WHERE id = 'users\\\\'", "users\\\\")
    is_not_sql_injection("SELECT * FROM users WHERE id = '\nusers'", "\nusers")
    is_not_sql_injection("SELECT * FROM users WHERE id = '\rusers'", "\rusers")
    is_not_sql_injection("SELECT * FROM users WHERE id = '\tusers'", "\tusers")


def test_user_input_inside_in():
    is_sql_injection("SELECT * FROM users WHERE id IN ('123')", "'123'")
    is_not_sql_injection("SELECT * FROM users WHERE id IN (123)", "123")
    is_not_sql_injection("SELECT * FROM users WHERE id IN (123, 456)", "123")
    is_not_sql_injection("SELECT * FROM users WHERE id IN (123, 456)", "456")
    is_not_sql_injection("SELECT * FROM users WHERE id IN ('123')", "123")
    is_not_sql_injection("SELECT * FROM users WHERE id IN (13,14,15)", "13,14,15")
    is_not_sql_injection("SELECT * FROM users WHERE id IN (13, 14, 154)", "13, 14, 154")
    is_sql_injection(
        "SELECT * FROM users WHERE id IN (13, 14, 154) OR (1=1)", "13, 14, 154) OR (1=1"
    )


def test_check_string_safely_escaped():
    is_sql_injection(
        "SELECT * FROM comments WHERE comment = 'I'm writting you'", "I'm writting you"
    )
    is_sql_injection(
        'SELECT * FROM comments WHERE comment = "I"m writting you"', 'I"m writting you'
    )
    is_sql_injection("SELECT * FROM `comm`ents`", "`comm`ents")
    is_not_sql_injection(
        'SELECT * FROM comments WHERE comment = "I\'m writting you"', "I'm writting you"
    )
    is_not_sql_injection(
        "SELECT * FROM comments WHERE comment = 'I\"m writting you'", 'I"m writting you'
    )
    is_not_sql_injection(
        'SELECT * FROM comments WHERE comment = "I\`m writting you"', "I`m writting you"
    )
    is_not_sql_injection("SELECT * FROM `comm'ents`", "comm'ents")


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
    is_sql_injection("SELECT * FROM users WHERE id = 'a'\nOR 1=1#'", "a'\nOR 1=1#")
    is_not_sql_injection("SELECT * FROM users WHERE id = 'a\nb\nc';", "a\nb\nc")


def test_user_input_is_longer_than_query():
    is_not_sql_injection("SELECT * FROM users", "SELECT * FROM users WHERE id = 'a'")


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

    assert is_sql_injection(sql, expected_sql_injection)


@pytest.mark.parametrize("dangerous", SQL_DANGEROUS_IN_STRING)
def test_dangerous_strings(dangerous):
    input = f"{dangerous} a"
    is_sql_injection(f"SELECT * FROM users WHERE {input}", input)


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

    is_not_sql_injection("foobar)", "foobar)")
    is_not_sql_injection("foobar      )", "foobar      )")
    is_not_sql_injection("€foobar()", "€foobar()")


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
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            sql = line.rstrip("\n")

            def test_sql_injection():
                assert is_sql_injection(sql, sql)

            def test_sql_injection_query():
                assert is_sql_injection(f"SELECT * FROM users WHERE id = {sql}", sql)
