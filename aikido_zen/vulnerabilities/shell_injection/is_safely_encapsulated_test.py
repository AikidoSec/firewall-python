import pytest
from .is_safely_encapsulated import is_safely_encapsulated


def test_safe_between_single_quotes():
    assert is_safely_encapsulated("echo '$USER'", "$USER") == True
    assert is_safely_encapsulated("echo '`$USER'", "`USER") == True


def test_single_quote_in_single_quotes():
    assert is_safely_encapsulated("echo ''USER'", "'USER") == False


def test_dangerous_chars_between_double_quotes():
    assert is_safely_encapsulated('echo "=USER"', "=USER") == True
    assert is_safely_encapsulated('echo "$USER"', "$USER") == False
    assert is_safely_encapsulated('echo "!USER"', "!USER") == False
    assert is_safely_encapsulated('echo "\\`USER"', "`USER") == False
    assert is_safely_encapsulated('echo "\\USER"', "\\USER") == False


def test_same_user_input_multiple_times():
    assert is_safely_encapsulated("echo '$USER' '$USER'", "$USER") == True
    assert is_safely_encapsulated("echo \"$USER\" '$USER'", "$USER") == False
    assert is_safely_encapsulated('echo "$USER" "$USER"', "$USER") == False


def test_first_and_last_quote_does_not_match():
    assert is_safely_encapsulated("echo '$USER\"", "$USER") == False
    assert is_safely_encapsulated("echo \"$USER'", "$USER") == False


def test_first_or_last_character_not_escape_char():
    assert is_safely_encapsulated("echo $USER'", "$USER") == False
    assert is_safely_encapsulated('echo $USER"', "$USER") == False


def test_user_input_does_not_occur_in_command():
    assert is_safely_encapsulated("echo 'USER'", "$USER") == True
    assert is_safely_encapsulated('echo "USER"', "$USER") == True
