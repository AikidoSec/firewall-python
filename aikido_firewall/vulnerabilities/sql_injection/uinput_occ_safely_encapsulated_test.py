import pytest
from aikido_firewall.vulnerabilities.sql_injection.uinput_occ_safely_encapsulated import (
    uinput_occ_safely_encapsulated,
)


def test_user_input_occurrences_safely_encapsulated():
    assert (
        uinput_occ_safely_encapsulated(
            " Hello Hello 'UNION'and also \"UNION\" ", "UNION"
        )
        == True
    )
    assert uinput_occ_safely_encapsulated('"UNION"', "UNION") == True
    assert uinput_occ_safely_encapsulated("`UNION`", "UNION") == True
    assert uinput_occ_safely_encapsulated("`U`NION`", "U`NION") == False
    assert uinput_occ_safely_encapsulated(" 'UNION' ", "UNION") == True
    assert (
        uinput_occ_safely_encapsulated("\"UNION\"'UNION'", "UNION") == True
    )
    assert (
        uinput_occ_safely_encapsulated("'UNION'\"UNION\"UNION", "UNION")
        == False
    )
    assert (
        uinput_occ_safely_encapsulated("'UNION'UNION\"UNION\"", "UNION")
        == False
    )
    assert uinput_occ_safely_encapsulated("UNION", "UNION") == False
    assert uinput_occ_safely_encapsulated('"UN\'ION"', "UN'ION") == True
    assert uinput_occ_safely_encapsulated("'UN\"ION'", 'UN"ION') == True
    assert (
        uinput_occ_safely_encapsulated(
            "SELECT * FROM cats WHERE id = 'UN\"ION' AND id = \"UN'ION\"", 'UN"ION'
        )
        == True
    )
    assert (
        uinput_occ_safely_encapsulated(
            "SELECT * FROM cats WHERE id = 'UN'ION' AND id = \"UN'ION\"", "UN'ION"
        )
        == False
    )
    assert (
        uinput_occ_safely_encapsulated(
            "SELECT * FROM cats WHERE id = 'UNION\\'", "UNION\\"
        )
        == False
    )
    assert (
        uinput_occ_safely_encapsulated(
            "SELECT * FROM cats WHERE id = 'UNION\\\\'", "UNION\\\\"
        )
        == False
    )
    assert (
        uinput_occ_safely_encapsulated(
            "SELECT * FROM cats WHERE id = 'UNION\\\\\\'", "UNION\\\\\\"
        )
        == False
    )
    assert (
        uinput_occ_safely_encapsulated(
            "SELECT * FROM cats WHERE id = 'UNION\\n'", "UNION\\n"
        )
        == True
    )
    assert (
        uinput_occ_safely_encapsulated(
            "SELECT * FROM users WHERE id = '\\'hello'", "'hello'"
        )
        == False
    )
    assert (
        uinput_occ_safely_encapsulated(
            'SELECT * FROM users WHERE id = "\\"hello"', '"hello"'
        )
        == False
    )


def test_surrounded_with_single_quotes():
    assert (
        uinput_occ_safely_encapsulated(
            "SELECT * FROM users WHERE id = '\\'hello\\''", "'hello'"
        )
        == True
    )


def test_surrounded_with_double_quotes():
    assert (
        uinput_occ_safely_encapsulated(
            'SELECT * FROM users WHERE id = "\\"hello\\""', '"hello"'
        )
        == True
    )


def test_starts_with_single_quote():
    assert (
        uinput_occ_safely_encapsulated(
            "SELECT * FROM users WHERE id = '\\' or true--'", "' or true--"
        )
        == True
    )


def test_starts_with_double_quote():
    assert (
        uinput_occ_safely_encapsulated(
            'SELECT * FROM users WHERE id = "\\" or true--"', '" or true--'
        )
        == True
    )


def test_starts_with_single_quote_without_sql_syntax():
    assert (
        uinput_occ_safely_encapsulated(
            "SELECT * FROM users WHERE id = '\\' hello world'", "' hello world"
        )
        == True
    )


def test_starts_with_double_quote_without_sql_syntax():
    assert (
        uinput_occ_safely_encapsulated(
            'SELECT * FROM users WHERE id = "\\" hello world"', '" hello world'
        )
        == True
    )


def test_starts_with_single_quote_multiple_occurrences():
    assert (
        uinput_occ_safely_encapsulated(
            "SELECT * FROM users WHERE id = '\\'hello' AND id = '\\'hello'", "'hello"
        )
        == True
    )
    assert (
        uinput_occ_safely_encapsulated(
            "SELECT * FROM users WHERE id = 'hello' AND id = '\\'hello'", "'hello"
        )
        == False
    )


def test_starts_with_double_quote_multiple_occurrences():
    assert (
        uinput_occ_safely_encapsulated(
            'SELECT * FROM users WHERE id = "\\"hello" AND id = "\\"hello"', '"hello'
        )
        == True
    )
    assert (
        uinput_occ_safely_encapsulated(
            'SELECT * FROM users WHERE id = "hello" AND id = "\\"hello"', '"hello'
        )
        == False
    )


def test_single_quotes_escaped_with_single_quotes():
    assert (
        uinput_occ_safely_encapsulated(
            "SELECT * FROM users WHERE id = '''&'''", "'&'"
        )
        == False
    )
