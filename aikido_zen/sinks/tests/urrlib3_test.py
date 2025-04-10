import os
import pytest
from aikido_zen.context import Context, current_context
from aikido_zen.thread.thread_cache import get_cache
from aikido_zen.errors import AikidoSSRF
from aikido_zen.background_process.comms import reset_comms
import aikido_zen.sinks.socket
import aikido_zen.sinks.http_client
import urllib3

SSRF_TEST = "http://ssrf-redirects.testssandbox.com/ssrf-test"
SSRF_TEST_DOMAIN = "http://ssrf-redirects.testssandbox.com/ssrf-test-domain"
SSRF_TEST_TWICE = "http://ssrf-redirects.testssandbox.com/ssrf-test-twice"
SSRF_TEST_DOMAIN_TWICE = "http://ssrf-redirects.testssandbox.com/ssrf-test-domain-twice"

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


def set_context_and_lifecycle(url, host=None):
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
    if host is not None:
        wsgi_request["HTTP_HOST"] = host
    context = Context(
        req=wsgi_request,
        body={
            "url": url,
        },
        source="flask",
    )
    context.set_as_current_context()


def test_srrf_test(monkeypatch):
    http = urllib3.PoolManager()
    reset_comms()
    set_context_and_lifecycle(SSRF_TEST)
    monkeypatch.setenv("AIKIDO_BLOCK", "1")

    with pytest.raises(AikidoSSRF):
        http.request("GET", SSRF_TEST)


def test_srrf_test_twice(monkeypatch):
    http = urllib3.PoolManager()
    set_context_and_lifecycle(SSRF_TEST_TWICE)
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSSRF):
        http.request("GET", SSRF_TEST_TWICE)


def test_srrf_test_domain(monkeypatch):
    http = urllib3.PoolManager()
    set_context_and_lifecycle(SSRF_TEST_DOMAIN)
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSSRF):
        http.request("GET", SSRF_TEST_DOMAIN)


def test_srrf_test_domain_with_aikido_blocking(monkeypatch):
    http = urllib3.PoolManager()
    set_context_and_lifecycle(SSRF_TEST_DOMAIN)
    monkeypatch.setenv("AIKIDO_BLOCKING", "1")
    with pytest.raises(AikidoSSRF):
        http.request("GET", SSRF_TEST_DOMAIN)


def test_srrf_test_domain_twice(monkeypatch):
    http = urllib3.PoolManager()
    set_context_and_lifecycle(SSRF_TEST_DOMAIN_TWICE)
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSSRF):
        http.request("GET", SSRF_TEST_DOMAIN_TWICE)


def test_cross_domain(monkeypatch):
    http = urllib3.PoolManager()
    set_context_and_lifecycle(CROSS_DOMAIN_TEST)
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSSRF):
        http.request("GET", CROSS_DOMAIN_TEST)


def test_cross_domain_test_domain_twice(monkeypatch):
    http = urllib3.PoolManager()
    set_context_and_lifecycle(CROSS_DOMAIN_TEST_DOMAIN_TWICE)
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSSRF):
        http.request("GET", CROSS_DOMAIN_TEST_DOMAIN_TWICE)


def test_no_raises_if_diff_url(monkeypatch):
    http = urllib3.PoolManager()
    set_context_and_lifecycle(CROSS_DOMAIN_TEST_DOMAIN_TWICE)
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(urllib3.exceptions.MaxRetryError):
        http.request("GET", SSRF_TEST_DOMAIN_TWICE)


def test_srrf_with_request_to_itself(monkeypatch):
    http = urllib3.PoolManager()
    reset_comms()

    set_context_and_lifecycle("http://localhost:5000/test/1", host="localhost:5000")
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(urllib3.exceptions.MaxRetryError):
        http.request("GET", "http://localhost:5000/test/1")

    # Now test with no port match
    set_context_and_lifecycle("http://localhost:5000/test/2", host="localhost:4999")
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSSRF):
        http.request("GET", "http://localhost:5000/test/2")

    # Test with http app requesting to https
    set_context_and_lifecycle("https://localhost/test/3", host="localhost:80")
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(urllib3.exceptions.MaxRetryError):
        http.request("GET", "https://localhost/test/3")

    # Test with https app requesting to http
    set_context_and_lifecycle("http://localhost/test/4", host="localhost:443")
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(urllib3.exceptions.MaxRetryError):
        http.request("GET", "https://localhost/test/4")
