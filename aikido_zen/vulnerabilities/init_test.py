import pytest
from unittest.mock import MagicMock, patch
from . import run_vulnerability_scan
from aikido_zen.context import current_context, Context
from aikido_zen.errors import AikidoSQLInjection
from aikido_zen.thread.thread_cache import get_cache
from aikido_zen.helpers.iplist import IPList


@pytest.fixture(autouse=True)
def run_around_tests():
    get_cache().reset()
    yield
    # Make sure to reset context and cache after every test so it does not
    # interfere with other tests
    current_context.set(None)
    get_cache().reset()


@pytest.fixture
def mock_comms():
    """Fixture to mock the get_comms function."""
    with patch("aikido_zen.background_process.comms.get_comms") as mock:
        yield mock


@pytest.fixture
def get_context():
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
        body={"test_input_sql": "doggoss2', TRUE"},
        source="flask",
    )
    context.route_params = {"test_input2": "cattss2', TRUE"}
    return context


def test_run_vulnerability_scan_no_context(caplog):
    current_context.set(None)
    get_cache().cache = 1
    run_vulnerability_scan(kind="test", op="test", args=tuple())
    assert len(caplog.text) == 0


def test_run_vulnerability_scan_no_context_no_lifecycle(caplog):
    current_context.set(None)
    get_cache().cache = None
    run_vulnerability_scan(kind="test", op="test", args=tuple())
    assert len(caplog.text) == 0


def test_run_vulnerability_scan_context_no_lifecycle(caplog):
    with pytest.raises(Exception):
        current_context.set(1)
        get_cache().cache = None
        run_vulnerability_scan(kind="test", op="test", args=tuple())


def test_lifecycle_cache_ok(caplog, get_context):
    get_context.set_as_current_context()
    run_vulnerability_scan(kind="test", op="test", args=tuple())
    assert "Vulnerability type test currently has no scans implemented" in caplog.text


def test_ssrf(caplog, get_context):
    current_context.set(None)
    run_vulnerability_scan(kind="ssrf", op="test", args=tuple())


def test_lifecycle_cache_bypassed_ip(caplog, get_context):
    get_context.set_as_current_context()
    cache = get_cache()
    cache.config.bypassed_ips = IPList()
    cache.config.bypassed_ips.add("198.51.100.23")
    assert cache.is_bypassed_ip("198.51.100.23")
    run_vulnerability_scan(kind="test", op="test", args=tuple())
    assert len(caplog.text) == 0


def test_sql_injection(caplog, get_context, monkeypatch):
    get_context.set_as_current_context()
    monkeypatch.setenv("AIKIDO_BLOCK", "1")

    assert get_cache().stats.get_record()["requests"]["attacksDetected"]["total"] == 0
    with pytest.raises(AikidoSQLInjection):
        run_vulnerability_scan(
            kind="sql_injection",
            op="test_op",
            args=("INSERT * INTO VALUES ('doggoss2', TRUE);", "mysql"),
        )
    assert get_cache().stats.get_record()["requests"]["attacksDetected"]["total"] == 1
    assert get_cache().stats.get_record()["requests"]["attacksDetected"]["blocked"] == 1


def test_sql_injection_but_blocking_off(caplog, get_context, monkeypatch):
    get_context.set_as_current_context()
    monkeypatch.setenv("AIKIDO_BLOCK", "0")

    assert get_cache().stats.get_record()["requests"]["attacksDetected"]["total"] == 0
    run_vulnerability_scan(
        kind="sql_injection",
        op="test_op",
        args=("INSERT * INTO VALUES ('doggoss2', TRUE);", "mysql"),
    )
    assert get_cache().stats.get_record()["requests"]["attacksDetected"]["total"] == 1
    assert get_cache().stats.get_record()["requests"]["attacksDetected"]["blocked"] == 0


def test_sql_injection_with_route_params(caplog, get_context, monkeypatch):
    get_context.set_as_current_context()
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with pytest.raises(AikidoSQLInjection):
        run_vulnerability_scan(
            kind="sql_injection",
            op="test_op",
            args=("INSERT * INTO VALUES ('cattss2', TRUE);", "mysql"),
        )


def test_sql_injection_with_comms(caplog, get_context, monkeypatch):
    get_context.set_as_current_context()
    monkeypatch.setenv("AIKIDO_BLOCK", "1")
    with patch("aikido_zen.background_process.comms.get_comms") as mock_get_comms:
        # Create a mock comms object
        mock_comms = MagicMock()
        mock_get_comms.return_value = mock_comms  # Set the return value of get_comms
        with pytest.raises(AikidoSQLInjection):
            run_vulnerability_scan(
                kind="sql_injection",
                op="test_op",
                args=("INSERT * INTO VALUES ('doggoss2', TRUE);", "mysql"),
            )
        mock_comms.send_data_to_bg_process.assert_called_once()
        call_args = mock_comms.send_data_to_bg_process.call_args[0]
        assert call_args[0] == "ATTACK"
        assert call_args[1][0]["kind"] == "sql_injection"
        assert (
            call_args[1][0]["metadata"]["sql"]
            == "INSERT * INTO VALUES ('doggoss2', TRUE);"
        )
        assert call_args[1][0]["metadata"]["dialect"] == "mysql"


def test_ssrf_vulnerability_scan_adds_hostname(get_context):
    get_context.set_as_current_context()

    dns_results = MagicMock()
    hostname = "example.com"
    port = 80

    run_vulnerability_scan(kind="ssrf", op="test", args=(dns_results, hostname, port))

    # Verify that hostnames.add was called with the correct arguments
    assert get_cache().hostnames.as_array() == [
        {"hits": 1, "hostname": "example.com", "port": 80}
    ]
    run_vulnerability_scan(kind="ssrf", op="test", args=(dns_results, hostname, port))
    assert get_cache().hostnames.as_array() == [
        {"hits": 2, "hostname": "example.com", "port": 80}
    ]


def test_ssrf_vulnerability_scan_no_port(get_context):
    get_context.set_as_current_context()

    dns_results = MagicMock()
    hostname = "example.com"
    port = 0  # Port is zero, should not add to hostnames

    assert get_cache().stats.get_record()["requests"]["attacksDetected"]["total"] == 0
    run_vulnerability_scan(kind="ssrf", op="test", args=(dns_results, hostname, port))
    assert get_cache().stats.get_record()["requests"]["attacksDetected"]["total"] == 0

    assert get_cache().hostnames.as_array() == []


def test_ssrf_vulnerability_scan_bypassed_ip(get_context):
    get_context.set_as_current_context()
    get_cache().config.bypassed_ips = IPList()
    get_cache().config.bypassed_ips.add("198.51.100.23")

    dns_results = MagicMock()
    hostname = "example.com"
    port = 80

    assert get_cache().stats.get_record()["requests"]["attacksDetected"]["total"] == 0
    run_vulnerability_scan(kind="ssrf", op="test", args=(dns_results, hostname, port))
    assert get_cache().stats.get_record()["requests"]["attacksDetected"]["total"] == 0

    # Verify that hostnames.add was not called due to bypassed IP
    assert get_cache().hostnames.as_array() == []
