import pytest
from .find_hostname_in_userinput import (
    find_hostname_in_userinput as _find_hostname_in_userinput,
)
from .get_hostname_options import get_hostname_options


def find_hostname_in_userinput(user_input, hostname, port=None):
    hostname_options = get_hostname_options(hostname)
    return _find_hostname_in_userinput(user_input, hostname_options, port)


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


def test_loopback_ipv6_found():
    assert find_hostname_in_userinput("http://[::1]:8081", "[::1]") is True


def test_loopback_ipv6_with_zeros_found():
    assert (
        find_hostname_in_userinput(
            "http://[0000:0000:0000:0000:0000:0000:0000:0001]:8081",
            "[0000:0000:0000:0000:0000:0000:0000:0001]",
        )
        is True
    )


def test_different_capitalization_found():
    assert find_hostname_in_userinput("http://localHost:8081", "localhost") is True


def test_2130706433_found():
    assert find_hostname_in_userinput("http://2130706433:8081", "2130706433") is True


def test_0x7f000001_found():
    assert find_hostname_in_userinput("http://0x7f000001:8081", "0x7f000001") is True


def test_0177_0_0_01_found():
    assert find_hostname_in_userinput("http://0177.0.0.01:8081", "0177.0.0.01") is True


def test_0x7f_0x0_0x0_0x1_found():
    assert (
        find_hostname_in_userinput("http://0x7f.0x0.0x0.0x1:8081", "0x7f.0x0.0x0.0x1")
        is True
    )


def test_ffff_127_0_0_1_found():
    assert (
        find_hostname_in_userinput(
            "http://[::ffff:127.0.0.1]:8081", "[::ffff:127.0.0.1]"
        )
        is True
    )


def test_loopback_ipv6_not_found():
    assert find_hostname_in_userinput("http://[::1]:8081", "localhost") is False


def test_loopback_ipv6_with_zeros_not_found():
    assert (
        find_hostname_in_userinput(
            "http://[0000:0000:0000:0000:0000:0000:0000:0001]:8081", "localhost"
        )
        is False
    )


def test_different_capitalization_not_found():
    assert find_hostname_in_userinput("http://localHost:8081", "example.com") is False


def test_2130706433_not_found():
    assert find_hostname_in_userinput("http://2130706433:8081", "example.com") is False


def test_0x7f000001_not_found():
    assert find_hostname_in_userinput("http://0x7f000001:8081", "example.com") is False


def test_0177_0_0_01_not_found():
    assert find_hostname_in_userinput("http://0177.0.0.01:8081", "example.com") is False


def test_0x7f_0x0_0x0_0x1_not_found():
    assert (
        find_hostname_in_userinput("http://0x7f.0x0.0x0.0x1:8081", "example.com")
        is False
    )


def test_ffff_127_0_0_1_not_found():
    assert (
        find_hostname_in_userinput("http://[::ffff:127.0.0.1]:8081", "example.com")
        is False
    )
