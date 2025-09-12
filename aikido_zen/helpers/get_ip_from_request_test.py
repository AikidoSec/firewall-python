import pytest
from .get_ip_from_request import (
    get_ip_from_request,
    is_ip,
    get_client_ip_from_header,
)
from .headers import Headers


@pytest.fixture(autouse=True)
def reset_environment_variables(monkeypatch):
    monkeypatch.delenv("AIKIDO_TRUST_PROXY", raising=False)
    monkeypatch.delenv("AIKIDO_CLIENT_IP_HEADER", raising=False)


def test_no_headers_and_no_remote_address(monkeypatch):
    # Test case 1: No headers and no remote address
    monkeypatch.setenv("AIKIDO_TRUST_PROXY", "false")
    assert get_ip_from_request(None, Headers()) is None
    monkeypatch.setenv("AIKIDO_TRUST_PROXY", "true")
    assert get_ip_from_request(None, Headers()) is None


def test_no_headers_and_remote_address(monkeypatch):
    # Test case 2: No headers and valid remote address
    monkeypatch.setenv("AIKIDO_TRUST_PROXY", "false")
    assert get_ip_from_request("1.2.3.4", Headers()) == "1.2.3.4"
    monkeypatch.setenv("AIKIDO_TRUST_PROXY", "true")
    assert get_ip_from_request("1.2.3.4", Headers()) == "1.2.3.4"


def test_x_forwarded_for_without_trust_proxy(monkeypatch):
    # Test case 3: x-forwarded-for without trust proxy
    monkeypatch.setenv("AIKIDO_TRUST_PROXY", "0")
    headers = Headers()
    headers.store_header("x-forwarded-for", "9.9.9.9")
    assert get_ip_from_request("1.2.3.4", headers) == "1.2.3.4"


def test_x_forwarded_for_without_trust_proxy_ipv6(monkeypatch):
    # Test case 3: x-forwarded-for without trust proxy
    monkeypatch.setenv("AIKIDO_TRUST_PROXY", "false")
    headers = Headers()
    headers.store_header("x-forwarded-for", "a3ad:8f95:d2a8:454b:cf19:be6e:73c6:f880")
    assert (
        get_ip_from_request("df89:84af:85e0:c55f:960c:341a:2cc6:734d", headers)
        == "df89:84af:85e0:c55f:960c:341a:2cc6:734d"
    )


def test_x_forwarded_for_with_trust_proxy_invalid_ip():
    # Test case 4: x-forwarded-for with trust proxy and invalid IP
    headers = Headers()
    headers.store_header("x-forwarded-for", "invalid")
    assert get_ip_from_request("1.2.3.4", headers) == "1.2.3.4"


def test_x_forwarded_for_with_trust_proxy_ip_with_port():
    # Test case 5: x-forwarded-for with trust proxy and IP contains port
    headers = Headers()
    headers.store_header("x-forwarded-for", "9.9.9.9:8080")
    assert get_ip_from_request("1.2.3.4", headers) == "9.9.9.9"


def test_x_forwarded_for_with_trust_proxy_and_trailing_comma():
    # Test case 6: x-forwarded-for with trailing comma
    headers = Headers()
    headers.store_header("x-forwarded-for", "9.9.9.9,")
    assert get_ip_from_request("1.2.3.4", headers) == "9.9.9.9"


def test_x_forwarded_for_with_trust_proxy_and_leading_comma():
    # Test case 6: x-forwarded-for with trailing comma
    headers = Headers()
    headers.store_header("x-forwarded-for", ",9.9.9.9,,")
    assert get_ip_from_request("1.2.3.4", headers) == "9.9.9.9"


def test_x_forwarded_for_with_trust_proxy_public_ip():
    # Test case 9: x-forwarded-for with trust proxy and public IP
    headers = Headers()
    headers.store_header("x-forwarded-for", "9.9.9.9")
    assert get_ip_from_request("1.2.3.4", headers) == "9.9.9.9"


def test_x_forwarded_for_with_trust_proxy_multiple_ips():
    # Test case 10: x-forwarded-for with trust proxy and multiple IPs
    headers = Headers()
    headers.store_header("x-forwarded-for", "9.9.9.9, 8.8.8.8, 7.7.7.7")
    assert get_ip_from_request("1.2.3.4", headers) == "9.9.9.9"


def test_x_forwarded_for_with_trust_proxy_multiple_ips_ipv6():
    # Test case 10: x-forwarded-for with trust proxy and multiple IPs
    headers = Headers()
    headers.store_header(
        "x-forwarded-for",
        "a3ad:8f95:d2a8:454b:cf19:be6e:73c6:f880, 3b07:2fba:0270:2149:5fc1:2049:5f04:2131, 791d:967e:428a:90b9:8f6f:4fcc:5d88:015d",
    )
    assert (
        get_ip_from_request("df89:84af:85e0:c55f:960c:341a:2cc6:734d", headers)
        == "a3ad:8f95:d2a8:454b:cf19:be6e:73c6:f880"
    )


def test_get_ip_from_different_header(monkeypatch):
    # Test case 1: No client IP header set, should return remote address
    monkeypatch.setenv("AIKIDO_TRUST_PROXY", "0")
    headers = Headers()
    headers.store_header("x-forwarded-for", "127.0.0.1, 192.168.0.1")
    assert get_ip_from_request("1.2.3.4", headers) == "1.2.3.4"

    # Test case 2: Client IP header set to "connecting-ip", should return that IP
    monkeypatch.setenv("AIKIDO_CLIENT_IP_HEADER", "connecting-ip")
    monkeypatch.setenv("AIKIDO_TRUST_PROXY", "1")
    headers = Headers()
    headers.store_header("x-forwarded-for", "127.0.0.1, 192.168.0.1")
    headers.store_header("connecting-ip", "9.9.9.9")
    assert get_ip_from_request("1.2.3.4", headers) == "9.9.9.9"

    # Test case 3: No client IP header set, should return remote address
    monkeypatch.setenv("AIKIDO_TRUST_PROXY", "0")
    headers = Headers()
    headers.store_header("x-forwarded-for", "127.0.0.1, 192.168.0.1")
    assert get_ip_from_request("1.2.3.4", headers) == "1.2.3.4"

    # Test case 4: Client IP header set to "connecting-IP" (case insensitive), should return that IP
    monkeypatch.setenv("AIKIDO_CLIENT_IP_HEADER", "connecting-IP")
    monkeypatch.setenv("AIKIDO_TRUST_PROXY", "1")
    headers = Headers()
    headers.store_header("x-forwarded-for", "127.0.0.1, 192.168.0.1")
    headers.store_header("connecting-ip", "9.9.9.9")
    assert get_ip_from_request("1.2.3.4", headers) == "9.9.9.9"

    # Test case 5: Client IP header is empty, should return x-forwarded-for address
    monkeypatch.setenv("AIKIDO_CLIENT_IP_HEADER", "")
    monkeypatch.setenv("AIKIDO_TRUST_PROXY", "1")
    headers = Headers()
    headers.store_header("x-forwarded-for", "5.6.7.8, 192.168.0.1")
    headers.store_header("connecting-ip", "9.9.9.9")
    assert get_ip_from_request("1.2.3.4", headers) == "5.6.7.8"

    # Test case 6: Valid client ip header, but trust proxy 0
    monkeypatch.setenv("AIKIDO_CLIENT_IP_HEADER", "connecting-ip")
    monkeypatch.setenv("AIKIDO_TRUST_PROXY", "0")
    headers = Headers()
    headers.store_header("x-forwarded-for", "127.0.0.1, 192.168.0.1")
    headers.store_header("connecting-ip", "9.9.9.9")
    assert get_ip_from_request("1.2.3.4", headers) == "1.2.3.4"


#  Test `is_ip` function :
def test_valid_ipv4():
    assert is_ip("192.168.1.1")  # Valid IPv4
    assert is_ip("255.255.255.255")  # Valid IPv4
    assert is_ip("0.0.0.0")  # Valid IPv4


def test_invalid_ipv4():
    assert not is_ip("256.256.256.256")  # Invalid IPv4
    assert not is_ip("192.168.1")  # Invalid IPv4
    assert not is_ip("abc.def.ghi.jkl")  # Invalid IPv4


def test_valid_ipv6():
    assert is_ip("::1")  # Valid IPv6 (loopback)
    assert is_ip("2001:0db8:85a3:0000:0000:8a2e:0370:7334")  # Valid IPv6


def test_invalid_ipv6():
    assert not is_ip("2001:db8:85a3::8a2e:370:7334:12345")  # Invalid IPv6
    assert not is_ip("::g")  # Invalid IPv6


#  Test `get_client_ip_from_header` function :
def test_get_client_ip_from_header():
    # Test cases with valid IPs
    assert get_client_ip_from_header("192.168.1.1") == "192.168.1.1"
    assert get_client_ip_from_header("192.168.1.1, 10.0.0.1") == "192.168.1.1"
    assert get_client_ip_from_header("10.0.0.1, 192.168.1.1") == "10.0.0.1"
    assert (
        get_client_ip_from_header("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
        == "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    )
    assert (
        get_client_ip_from_header(
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334, 192.168.1.1"
        )
        == "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    )

    # Test cases with mixed valid and invalid IPs
    assert (
        get_client_ip_from_header("256.256.256.256, 192.168.1.1") == "192.168.1.1"
    )  # Invalid IPv4 ignored
    assert (
        get_client_ip_from_header("192.168.1.1, abc.def.ghi.jkl") == "192.168.1.1"
    )  # Invalid IPv4 ignored
    assert (
        get_client_ip_from_header("::1, 2001:0db8:85a3:0000:0000:8a2e:0370:7334")
        == "::1"
    )  # Valid IPv6 preferred

    # Test cases with only invalid IPs
    assert (
        get_client_ip_from_header("abc.def.ghi.jkl, 256.256.256.256") is None
    )  # All invalid
    assert get_client_ip_from_header("") is None  # Empty string
