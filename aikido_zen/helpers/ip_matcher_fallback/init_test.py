import pytest
from . import IPMatcher


def test_single_ipv4s():
    input_list = [
        "192.168.0.0/32",
        "192.168.0.3/32",
        "192.168.0.24/32",
        "192.168.0.52/32",
        "192.168.0.123/32",
        "192.168.0.124/32",
        "192.168.0.125/32",
        "192.168.0.170/32",
        "192.168.0.171/32",
        "192.168.0.222/32",
        "192.168.0.234/32",
        "192.168.0.255/32",
    ]
    matcher = IPMatcher(input_list)
    assert matcher.has("192.168.0.254") == False
    assert matcher.has("192.168.0.1") == False
    assert matcher.has("192.168.0.255") == True
    assert matcher.has("192.168.0.24") == True


def test_with_ranges():
    input_list = [
        "192.168.0.0/24",
        "192.168.0.3/32",
        "192.168.0.24/32",
        "192.168.0.52/32",
        "192.168.0.123/32",
        "192.168.0.124/32",
        "192.168.0.125/32",
        "192.168.0.170/32",
        "192.168.0.171/32",
        "192.168.0.222/32",
        "192.168.0.234/32",
        "192.168.0.255/32",
    ]
    matcher = IPMatcher(input_list)
    assert matcher.has("192.168.0.254") == True  # Now included because of the /24 range
    assert matcher.has("10.0.0.1") == False
    assert matcher.has("192.168.0.234") == True


def test_with_invalid_ranges():
    input_list = [
        "192.168.0.0/24",
        "192.168.0.3/32",
        "192.168.0.24/32",
        "192.168.0.52/32",
        "foobar",
        "0.a.0.0/32",
        "123.123.123.123/1999",
        "",
        ",,,",
        "192.168.0.124/32",
        "192.168.0.125/32",
        "192.168.0.170/32",
        "192.168.0.171/32",
        "192.168.0.222/32",
        "192.168.0.234/32",
        "192.168.0.255",
    ]
    matcher = IPMatcher(input_list)
    assert matcher.has("192.168.0.254") == True
    assert matcher.has("foobar") == False
    assert matcher.has("192.168.0.222") == True
    assert matcher.has("192.168.0.1") == True
    assert matcher.has("10.0.0.1") == False
    assert matcher.has("192.168.0.255") == True
    assert matcher.has("") == False
    assert matcher.has("1") == False
    assert matcher.has("192.168.0.1/32") == True


def test_with_empty_ranges():
    input_list = []
    matcher = IPMatcher(input_list)
    assert matcher.has("192.168.2.1") == False
    assert matcher.has("foobar") == False


def test_with_ipv6_ranges():
    input_list = [
        "2002:db8::/32",
        "2001:db8::1/128",
        "2001:db8::2/128",
        "2001:db8::3/128",
        "2001:db8::4/128",
        "2001:db8::5/128",
        "2001:db8::6/128",
        "2001:db8::7/128",
        "2001:db8::8/128",
        "2001:db8::9/128",
        "2001:db8::a/128",
        "2001:db8::b/128",
        "2001:db8::c/128",
        "2001:db8::d/128",
        "2001:db8::e/128",
        "[2001:db8::f]",
        "2001:db9::abc",
    ]
    matcher = IPMatcher(input_list)
    assert matcher.has("2001:db8::1") == True
    assert matcher.has("2001:db8::0") == False
    assert matcher.has("2001:db8::f") == True
    assert matcher.has("[2001:db8::f]") == True
    assert matcher.has("2001:db8::10") == False
    assert matcher.has("2002:db8::1") == True
    assert matcher.has("2002:db8::2f:2") == True
    assert matcher.has("2001:db9::abc") == True


def test_mix_ipv4_and_ipv6():
    input_list = ["2002:db8::/32", "10.0.0.0/8"]
    matcher = IPMatcher(input_list)
    assert matcher.has("2001:db8::1") == False
    assert matcher.has("2001:db8::0") == False
    assert matcher.has("2002:db8::1") == True
    assert matcher.has("10.0.0.1") == True
    assert matcher.has("10.0.0.255") == True
    assert matcher.has("192.168.1.1") == False


def test_add_ips_later():
    input_list = ["2002:db8::/32", "10.0.0.0/8"]
    matcher = IPMatcher()
    assert matcher.has("2001:db8::0") == False
    assert matcher.has("2002:db8::1") == False
    for ip in input_list:
        matcher.add(ip)
    assert matcher.has("2001:db8::1") == False
    assert matcher.has("2001:db8::0") == False
    assert matcher.has("2002:db8::1") == True
    assert matcher.has("10.0.0.1") == True
    assert matcher.has("10.0.0.255") == True
    assert matcher.has("192.168.1.1") == False


def test_strange_ips():
    input_list = ["::ffff:0.0.0.0", "::ffff:0:0:0:0", "::ffff:127.0.0.1"]
    matcher = IPMatcher(input_list)
    assert matcher.has("::ffff:0.0.0.0") == True
    assert matcher.has("::ffff:127.0.0.1") == True
    assert matcher.has("::ffff:123") == False
    assert matcher.has("2001:db8::1") == False
    assert matcher.has("[::ffff:0.0.0.0]") == True
    assert matcher.has("::ffff:0:0:0:0") == True


def test_different_cidr_ranges():
    assert IPMatcher(["123.2.0.2/0"]).has("1.1.1.1") == True
    assert IPMatcher(["123.2.0.2/1"]).has("1.1.1.1") == True
    assert IPMatcher(["123.2.0.2/2"]).has("1.1.1.1") == False
    assert IPMatcher(["123.2.0.2/3"]).has("123.3.0.1") == True
    assert IPMatcher(["123.2.0.2/4"]).has("123.3.0.1") == True
    assert IPMatcher(["123.2.0.2/5"]).has("123.3.0.1") == True
    assert IPMatcher(["123.2.0.2/6"]).has("123.3.0.1") == True
    assert IPMatcher(["123.2.0.2/7"]).has("123.3.0.1") == True
    assert IPMatcher(["123.2.0.2/8"]).has("123.3.0.1") == True
    assert IPMatcher(["123.2.0.2/9"]).has("123.3.0.1") == True
    assert IPMatcher(["123.2.0.2/10"]).has("123.3.0.1") == True
    assert IPMatcher(["123.2.0.2/11"]).has("123.3.0.1") == True
    assert IPMatcher(["123.2.0.2/12"]).has("123.3.0.1") == True
    assert IPMatcher(["123.2.0.2/13"]).has("123.3.0.1") == True
    assert IPMatcher(["123.2.0.2/14"]).has("123.3.0.1") == True
    assert IPMatcher(["123.2.0.2/15"]).has("123.3.0.1") == True
    assert IPMatcher(["123.2.0.2/16"]).has("123.3.0.1") == False
    assert IPMatcher(["123.2.0.2/17"]).has("123.2.0.1") == True
    assert IPMatcher(["123.2.0.2/18"]).has("123.2.0.1") == True
    assert IPMatcher(["123.2.0.2/19"]).has("123.2.0.1") == True
    assert IPMatcher(["123.2.0.2/20"]).has("123.2.0.1") == True
    assert IPMatcher(["123.2.0.2/21"]).has("123.2.0.1") == True
    assert IPMatcher(["123.2.0.2/22"]).has("123.2.0.1") == True
    assert IPMatcher(["123.2.0.2/23"]).has("123.2.0.1") == True
    assert IPMatcher(["123.2.0.2/24"]).has("123.2.0.1") == True
    assert IPMatcher(["123.2.0.2/25"]).has("123.2.0.1") == True
    assert IPMatcher(["123.2.0.2/26"]).has("123.2.0.1") == True
    assert IPMatcher(["123.2.0.2/27"]).has("123.2.0.1") == True
    assert IPMatcher(["123.2.0.2/29"]).has("123.2.0.1") == True
    assert IPMatcher(["123.2.0.2/30"]).has("123.2.0.1") == True
    assert IPMatcher(["123.2.0.2/31"]).has("123.2.0.1") == False
    assert IPMatcher(["123.2.0.2/32"]).has("123.2.0.2") == True


def test_allow_all_ips():
    matcher = IPMatcher(["0.0.0.0/0", "::/0"])
    assert matcher.has("1.2.3.4") == True
    assert matcher.has("::1") == True
    assert matcher.has("::ffff:1234") == True
    assert matcher.has("1.1.1.1") == True
    assert matcher.has("2002:db8::1") == True
    assert matcher.has("10.0.0.1") == True
    assert matcher.has("10.0.0.255") == True
    assert matcher.has("192.168.1.1") == True
