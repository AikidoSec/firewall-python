import os
import pytest
from aikido_zen.context import Context
from aikido_zen.background_process.ipc_lifecycle_cache import IPCLifecycleCache
from aikido_zen.errors import AikidoSSRF
from aikido_zen.background_process.comms import reset_comms
import aikido_zen.sinks.socket
import aikido_zen.sinks.http_client
import requests

SSRF_TEST = "http://firewallssrfredirects-env-2.eba-7ifve22q.eu-north-1.elasticbeanstalk.com/ssrf-test"
SSRF_TEST_DOMAIN = "http://firewallssrfredirects-env-2.eba-7ifve22q.eu-north-1.elasticbeanstalk.com/ssrf-test-domain"
SSRF_TEST_TWICE = "http://firewallssrfredirects-env-2.eba-7ifve22q.eu-north-1.elasticbeanstalk.com/ssrf-test-twice"
SSRF_TEST_DOMAIN_TWICE = "http://firewallssrfredirects-env-2.eba-7ifve22q.eu-north-1.elasticbeanstalk.com/ssrf-test-domain-twice"

CROSS_DOMAIN_TEST = "http://ec2-13-60-120-68.eu-north-1.compute.amazonaws.com/ssrf-test"
CROSS_DOMAIN_TEST_DOMAIN_TWICE = (
    "http://ec2-13-60-120-68.eu-north-1.compute.amazonaws.com/ssrf-test-domain-twice"
)


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
    IPCLifecycleCache(context)


def test_srrf_test(monkeypatch):
    reset_comms()
    set_context_and_lifecycle(SSRF_TEST)
    monkeypatch.setenv("AIKIDO_BLOCKING", "1")

    with pytest.raises(AikidoSSRF):
        requests.get(SSRF_TEST)


def test_srrf_test_twice(monkeypatch):
    set_context_and_lifecycle(SSRF_TEST_TWICE)
    monkeypatch.setenv("AIKIDO_BLOCKING", "1")
    with pytest.raises(AikidoSSRF):
        requests.get(SSRF_TEST_TWICE)


def test_srrf_test_domain(monkeypatch):
    set_context_and_lifecycle(SSRF_TEST_DOMAIN)
    monkeypatch.setenv("AIKIDO_BLOCKING", "1")
    with pytest.raises(AikidoSSRF):
        requests.get(SSRF_TEST_DOMAIN)


def test_srrf_test_domain_twice(monkeypatch):
    set_context_and_lifecycle(SSRF_TEST_DOMAIN_TWICE)
    monkeypatch.setenv("AIKIDO_BLOCKING", "1")
    with pytest.raises(AikidoSSRF):
        requests.get(SSRF_TEST_DOMAIN_TWICE)


def test_cross_domain(monkeypatch):
    set_context_and_lifecycle(CROSS_DOMAIN_TEST)
    monkeypatch.setenv("AIKIDO_BLOCKING", "1")
    with pytest.raises(AikidoSSRF):
        requests.get(CROSS_DOMAIN_TEST)


def test_cross_domain_test_domain_twice(monkeypatch):
    set_context_and_lifecycle(CROSS_DOMAIN_TEST_DOMAIN_TWICE)
    monkeypatch.setenv("AIKIDO_BLOCKING", "1")
    with pytest.raises(AikidoSSRF):
        requests.get(CROSS_DOMAIN_TEST_DOMAIN_TWICE)


def test_no_raises_if_diff_url(monkeypatch):
    set_context_and_lifecycle(CROSS_DOMAIN_TEST_DOMAIN_TWICE)
    monkeypatch.setenv("AIKIDO_BLOCKING", "1")
    with pytest.raises(requests.exceptions.ConnectionError):
        requests.get(SSRF_TEST_DOMAIN_TWICE)
