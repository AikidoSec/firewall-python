import os
import pytest

from aikido_zen.context import Context, current_context
from aikido_zen.thread.thread_cache import ThreadCache, get_cache
from aikido_zen.errors import AikidoSSRF
from aikido_zen.background_process.comms import reset_comms
import aikido_zen.sinks.socket
import aikido_zen.sinks.http_client
import requests
import urllib3
from requests import ConnectTimeout


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


def ssrf_check(monkeypatch, url, requests_only=False):
    reset_comms()
    set_context_and_lifecycle(url)
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSSRF):
        requests.get(url)
    if requests_only:
        return
    with pytest.raises(AikidoSSRF):
        http = urllib3.PoolManager()
        http.request("GET", url)


@pytest.mark.parametrize(
    "url",
    [
        # ssrf test
        "http://ssrf-redirects.testssandbox.com/ssrf-test",
        # twice ssrf test
        "http://ssrf-redirects.testssandbox.com/ssrf-test-twice",
        # domain test
        "http://ssrf-redirects.testssandbox.com/ssrf-test-domain",
        # domain twice test
        "http://ssrf-redirects.testssandbox.com/ssrf-test-domain-twice",
        # punycode test
        "http://ssrf-rédirects.testssandbox.com/ssrf-test",
        # Punycode encoded test
        "http://xn--ssrf-rdirects-ghb.testssandbox.com/ssrf-test",
        # Punycode domain twice test
        "http://ssrf-rédirects.testssandbox.com/ssrf-test-domain-twice",
        # cross domain test
        "http://firewallssrfredirects-env-2.eba-7ifve22q.eu-north-1.elasticbeanstalk.com/ssrf-test",
        # cross domain test twice
        "http://firewallssrfredirects-env-2.eba-7ifve22q.eu-north-1.elasticbeanstalk.com/ssrf-test-domain-twice",
        # loopback ipv6
        "http://[::1]:8081",
        "http://[::1]:8081/",
        "http://[::1]:8081/test",
        # loopback ipv6 with zeroes
        "http://[0000:0000:0000:0000:0000:0000:0000:0001]:8081",
        "http://[0000:0000:0000:0000:0000:0000:0000:0001]:8081/",
        "http://[0000:0000:0000:0000:0000:0000:0000:0001]:8081/test",
        # private ips written differently
        "http://2130706433:8081",
        "http://0x7f000001:8081/",
        "http://0x7f.0x0.0x0.0x1:8081/",
        # 127.0.0.1 ipv6 mapped
        "http://[::ffff:127.0.0.1]:8081",
    ],
)
def test_ssrf_1(monkeypatch, url):
    ssrf_check(monkeypatch, url)


def test_no_raises_if_diff_url(monkeypatch):
    set_context_and_lifecycle(
        "http://firewallssrfredirects-env-2.eba-7ifve22q.eu-north-1.elasticbeanstalk.com/ssrf-test-domain-twice"
    )
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(requests.exceptions.ConnectionError):
        requests.get("http://ssrf-redirects.testssandbox.com/ssrf-test-domain-twice")


def test_no_raises_if_diff_url_urllib3(monkeypatch):
    http = urllib3.PoolManager()
    set_context_and_lifecycle(
        "http://firewallssrfredirects-env-2.eba-7ifve22q.eu-north-1.elasticbeanstalk.com/ssrf-test-domain-twice"
    )
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(urllib3.exceptions.MaxRetryError):
        http.request(
            "GET", "http://ssrf-redirects.testssandbox.com/ssrf-test-domain-twice"
        )


def test_localhost_is_same_as_context(monkeypatch):
    set_context_and_lifecycle("http://localhost:8080")
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(requests.exceptions.ConnectionError):
        requests.get("http://localhost:8080")


def test_localhost_raises_ssrf(monkeypatch):
    set_context_and_lifecycle("http://localhost:8081/")
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSSRF):
        requests.get("http://localhost:8081")
    with pytest.raises(AikidoSSRF):
        requests.get("http://localhost:8081/")
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


def test_different_capitalization_raises_ssrf(monkeypatch):
    set_context_and_lifecycle("http://localHost:8081")
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSSRF):
        requests.get("http://LOCALHOST:8081")
    with pytest.raises(AikidoSSRF):
        requests.get("http://Localhost:8081/")
    with pytest.raises(AikidoSSRF):
        requests.get("http://localHost:8081/test")


def test_srrf_with_request_to_itself_urllib3(monkeypatch):
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


def test_ssrf_encoded_chars(monkeypatch):
    # This type of URL only works for requests
    ssrf_check(monkeypatch, "http://127%2E0%2E0%2E1:4000", requests_only=True)


def test_zero_padded_ip(monkeypatch):
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    reset_comms()

    url = "http://0127.0.0.01:5000"
    set_context_and_lifecycle(url)
    # Can raise both errors : either connection times out -> 0127.0.0.01 not supported by platform
    # or it raises ssrf bug -> 0127.0.0.01 supported by platform
    with pytest.raises((AikidoSSRF, ConnectTimeout)):
        requests.get(url)
