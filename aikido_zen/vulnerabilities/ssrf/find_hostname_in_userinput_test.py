import pytest
from .find_hostname_in_userinput import find_hostname_in_userinput


def test_returns_false_if_user_input_and_hostname_are_empty():
    assert find_hostname_in_userinput("", "") is False


def test_returns_false_if_user_input_is_empty():
    assert find_hostname_in_userinput("", "example.com") is False


def test_returns_false_if_hostname_is_empty():
    assert find_hostname_in_userinput("http://example.com", "") is False


def test_it_parses_hostname_from_user_input():
    assert find_hostname_in_userinput("http://localhost", "localhost") is True


def test_it_parses_special_ip():
    assert find_hostname_in_userinput("http://localhost", "localhost") is True


def test_it_parses_hostname_from_user_input_with_path_behind_it():
    assert find_hostname_in_userinput("http://localhost/path", "localhost") is True


def test_it_does_not_parse_hostname_from_user_input_with_misspelled_protocol():
    assert find_hostname_in_userinput("http:/localhost", "localhost") is False


def test_it_does_not_parse_hostname_from_user_input_without_protocol_separator():
    assert find_hostname_in_userinput("http:localhost", "localhost") is False


def test_it_does_not_parse_hostname_from_user_input_with_misspelled_protocol_and_path_behind_it():
    assert find_hostname_in_userinput("http:/localhost/path/path", "localhost") is False


def test_it_parses_hostname_from_user_input_without_protocol_and_path_behind_it():
    assert find_hostname_in_userinput("localhost/path/path", "localhost") is True


def test_it_flags_ftp_as_protocol():
    assert find_hostname_in_userinput("ftp://localhost", "localhost") is True


def test_it_parses_hostname_from_user_input_without_protocol():
    assert find_hostname_in_userinput("localhost", "localhost") is True


def test_it_ignores_invalid_urls():
    assert find_hostname_in_userinput("http://", "localhost") is False


def test_user_input_is_smaller_than_hostname():
    assert find_hostname_in_userinput("localhost", "localhost localhost") is False


def test_it_finds_ip_address_inside_url():
    assert (
        find_hostname_in_userinput(
            "http://169.254.169.254/latest/meta-data/", "169.254.169.254"
        )
        is True
    )


def test_it_finds_ip_address_with_strange_notation_inside_url():
    assert find_hostname_in_userinput("http://2130706433", "2130706433") is True
    assert find_hostname_in_userinput("http://127.1", "127.1") is True
    assert find_hostname_in_userinput("http://127.0.1", "127.0.1") is True


def test_it_works_with_invalid_ports():
    assert (
        find_hostname_in_userinput(
            "http://localhost:1337\\u0000asd.php", "localhost", 1337
        )
        is True
    )


def test_it_works_with_ports():
    assert find_hostname_in_userinput("http://localhost", "localhost", 8080) is False
    assert (
        find_hostname_in_userinput("http://localhost:8080", "localhost", 8080) is True
    )
    assert find_hostname_in_userinput("http://localhost:8080", "localhost") is True
    assert (
        find_hostname_in_userinput("http://localhost:8080", "localhost", 4321) is False
    )
