from .get_hostname_options import get_hostname_options


def test_plain_hostname():
    assert get_hostname_options("example.com") == ["example.com"]


def test_valid_punycode_adds_decoded_form():
    options = get_hostname_options("xn--r8jz45g.com")
    assert "xn--r8jz45g.com" in options
    assert len(options) > 1  # decoded variant added


def test_malformed_punycode_does_not_raise():
    # Invalid punycode labels (e.g. xn--a) previously raised UnicodeError
    # and aborted the whole SSRF scan. The raw hostname must still be returned.
    assert get_hostname_options("xn--a.com") == ["xn--a.com"]


def test_malformed_punycode_subdomain_does_not_raise():
    assert get_hostname_options("xn--a.attacker.com") == ["xn--a.attacker.com"]
