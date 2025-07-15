import os
import pytest
from aikido_zen.context import Context, current_context
from aikido_zen.thread.thread_cache import ThreadCache, get_cache
from aikido_zen.errors import AikidoSSRF
from aikido_zen.background_process.comms import reset_comms
import aikido_zen.sinks.socket
import aikido_zen.sinks.http_client
import requests

SSRF_TEST = "http://ssrf-redirects.testssandbox.com/ssrf-test"
SSRF_TEST_DOMAIN = "http://ssrf-redirects.testssandbox.com/ssrf-test-domain"
SSRF_TEST_TWICE = "http://ssrf-redirects.testssandbox.com/ssrf-test-twice"
SSRF_TEST_DOMAIN_TWICE = "http://ssrf-redirects.testssandbox.com/ssrf-test-domain-twice"

SSRF_TEST_PUNYCODE = "http://ssrf-rédirects.testssandbox.com/ssrf-test"
SSRF_TEST_PUNYCODE_ENCODED = "http://xn--ssrf-rdirects-ghb.testssandbox.com/ssrf-test"
SSRF_TEST_DOMAIN_TWICE_PUNYCODE = (
    "http://ssrf-rédirects.testssandbox.com/ssrf-test-domain-twice"
)


CROSS_DOMAIN_TEST = "http://firewallssrfredirects-env-2.eba-7ifve22q.eu-north-1.elasticbeanstalk.com/ssrf-test"
CROSS_DOMAIN_TEST_DOMAIN_TWICE = "http://firewallssrfredirects-env-2.eba-7ifve22q.eu-north-1.elasticbeanstalk.com/ssrf-test-domain-twice"


@pytest.fixture(autouse=True)
def run_around_tests():
    get_cache().reset()
    yield
    # Make sure to reset context and cache after every test so it does not
    # interfere with other tests
    current_context.set(None)
    get_cache().reset()


def set_context_and_lifecycle(url):
    wsgi_request = {
        "REQUEST_METHOD": "GET",
        "HTTP_HEADER_1": "header 1 value",
        "HTTP_HEADER_2": "Header 2 value",
        "RANDOM_VALUE": "Random value",
        "HTTP_COOKIE": "sessionId=abc123xyz456;",
        "wsgi.url_scheme": "http",
        "HTTP_HOST": "localhost:8080",
        "PATH_INFO": "/hello",
        "QUERY_STRING": "user=JohnDoe&age=30&age=35",
        "CONTENT_TYPE": "application/json",
        "REMOTE_ADDR": "198.51.100.23",
    }
    context = Context(
        req=wsgi_request,
        body={
            "url": url,
        },
        source="flask",
    )
    context.set_as_current_context()


def test_srrf_test(monkeypatch):
    reset_comms()
    set_context_and_lifecycle(SSRF_TEST)
    monkeypatch.setenv("AIKIDO_BLOCK", "1")

    with pytest.raises(AikidoSSRF):
        requests.get(SSRF_TEST)


def test_srrf_test_twice(monkeypatch):
    set_context_and_lifecycle(SSRF_TEST_TWICE)
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSSRF):
        requests.get(SSRF_TEST_TWICE)


def test_srrf_test_domain(monkeypatch):
    set_context_and_lifecycle(SSRF_TEST_DOMAIN)
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSSRF):
        requests.get(SSRF_TEST_DOMAIN)


def test_srrf_test_domain_twice(monkeypatch):
    set_context_and_lifecycle(SSRF_TEST_DOMAIN_TWICE)
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSSRF):
        requests.get(SSRF_TEST_DOMAIN_TWICE)


def test_ssrf_test_punycode(monkeypatch):
    reset_comms()
    set_context_and_lifecycle(SSRF_TEST_PUNYCODE)
    monkeypatch.setenv("AIKIDO_BLOCK", "1")

    with pytest.raises(AikidoSSRF):
        requests.get(SSRF_TEST_PUNYCODE)


def test_ssrf_test_punycode_encoded(monkeypatch):
    reset_comms()
    set_context_and_lifecycle(SSRF_TEST_PUNYCODE_ENCODED)
    monkeypatch.setenv("AIKIDO_BLOCK", "1")

    with pytest.raises(AikidoSSRF):
        requests.get(SSRF_TEST_PUNYCODE_ENCODED)


def test_ssrf_test_domain_twice_punycode(monkeypatch):
    reset_comms()
    set_context_and_lifecycle(SSRF_TEST_DOMAIN_TWICE_PUNYCODE)
    monkeypatch.setenv("AIKIDO_BLOCK", "1")

    with pytest.raises(AikidoSSRF):
        requests.get(SSRF_TEST_DOMAIN_TWICE_PUNYCODE)


def test_cross_domain(monkeypatch):
    set_context_and_lifecycle(CROSS_DOMAIN_TEST)
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSSRF):
        requests.get(CROSS_DOMAIN_TEST)


def test_cross_domain_test_domain_twice(monkeypatch):
    set_context_and_lifecycle(CROSS_DOMAIN_TEST_DOMAIN_TWICE)
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSSRF):
        requests.get(CROSS_DOMAIN_TEST_DOMAIN_TWICE)


def test_no_raises_if_diff_url(monkeypatch):
    set_context_and_lifecycle(CROSS_DOMAIN_TEST_DOMAIN_TWICE)
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(requests.exceptions.ConnectionError):
        requests.get(SSRF_TEST_DOMAIN_TWICE)


def test_localhost_is_same_as_context(monkeypatch):
    set_context_and_lifecycle("http://localhost:8080")
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(requests.exceptions.ConnectionError):
        requests.get("http://localhost:8080")


def test_localhost_raises_ssrf(monkeypatch):
    set_context_and_lifecycle("http://localhost:8081")
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSSRF):
        requests.get("http://localhost:8081")
    with pytest.raises(AikidoSSRF):
        requests.get("http://localhost:8081/test")
    with pytest.raises(requests.exceptions.ConnectionError):
        requests.get("http://localhost:5002/test")

    set_context_and_lifecycle("http://localhost:8081/test")
    with pytest.raises(AikidoSSRF):
        requests.get("http://localhost:8081/test")
    set_context_and_lifecycle("http://localhost:8081/test/2")
    with pytest.raises(AikidoSSRF):
        requests.get("http://localhost:8081/chicken/3")


def test_loopback_ipv6_raises_ssrf(monkeypatch):
    set_context_and_lifecycle("http://[::1]:8081")
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSSRF):
        requests.get("http://[::1]:8081")
    with pytest.raises(AikidoSSRF):
        requests.get("http://[::1]:8081/")
    with pytest.raises(AikidoSSRF):
        requests.get("http://[::1]:8081/test")


def test_loopback_ipv6_with_zeros_raises_ssrf(monkeypatch):
    set_context_and_lifecycle("http://[0000:0000:0000:0000:0000:0000:0000:0001]:8081")
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSSRF):
        requests.get("http://[0000:0000:0000:0000:0000:0000:0000:0001]:8081")
    with pytest.raises(AikidoSSRF):
        requests.get("http://[0000:0000:0000:0000:0000:0000:0000:0001]:8081/")
    with pytest.raises(AikidoSSRF):
        requests.get("http://[0000:0000:0000:0000:0000:0000:0000:0001]:8081/test")


def test_different_capitalization_raises_ssrf(monkeypatch):
    set_context_and_lifecycle("http://localHost:8081")
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSSRF):
        requests.get("http://LOCALHOST:8081")
    with pytest.raises(AikidoSSRF):
        requests.get("http://Localhost:8081/")
    with pytest.raises(AikidoSSRF):
        requests.get("http://localHost:8081/test")


def test_2130706433_raises_ssrf(monkeypatch):
    set_context_and_lifecycle("http://2130706433:8081")
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSSRF):
        requests.get("http://2130706433:8081")
    with pytest.raises(AikidoSSRF):
        requests.get("http://2130706433:8081/")
    with pytest.raises(AikidoSSRF):
        requests.get("http://2130706433:8081/test")


def test_0x7f000001_raises_ssrf(monkeypatch):
    set_context_and_lifecycle("http://0x7f000001:8081/")
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSSRF):
        requests.get("http://0x7f000001:8081")
    with pytest.raises(AikidoSSRF):
        requests.get("http://0x7f000001:8081/")
    with pytest.raises(AikidoSSRF):
        requests.get("http://0x7f000001:8081/test")


def test_0177_0_0_01_raises_ssrf(monkeypatch):
    set_context_and_lifecycle("http://0177.0.0.01:8081/")
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSSRF):
        requests.get("http://0177.0.0.01:8081/api/pets")
    with pytest.raises(AikidoSSRF):
        requests.get("http://0177.0.0.01:8081/")
    with pytest.raises(AikidoSSRF):
        requests.get("http://0177.0.0.01:8081/test")


def test_0x7f_0x0_0x0_0x1_raises_ssrf(monkeypatch):
    set_context_and_lifecycle("http://0x7f.0x0.0x0.0x1:8081/")
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSSRF):
        requests.get("http://0x7f.0x0.0x0.0x1:8081/api/pets")
    with pytest.raises(AikidoSSRF):
        requests.get("http://0x7f.0x0.0x0.0x1:8081/")
    with pytest.raises(AikidoSSRF):
        requests.get("http://0x7f.0x0.0x0.0x1:8081/test")


def test_ffff_127_0_0_1_raises_ssrf(monkeypatch):
    set_context_and_lifecycle("http://[::ffff:127.0.0.1]:8081")
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSSRF):
        requests.get("http://[::ffff:127.0.0.1]:8081")
    with pytest.raises(AikidoSSRF):
        requests.get("http://[::ffff:127.0.0.1]:8081/")
    with pytest.raises(AikidoSSRF):
        requests.get("http://[::ffff:127.0.0.1]:8081/test")
