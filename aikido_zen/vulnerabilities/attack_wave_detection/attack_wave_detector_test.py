import pytest
from unittest.mock import patch
from .attack_wave_detector import AttackWaveDetector


class Context:
    def __init__(self, route, method, ip):
        self.remote_address = ip
        self.method = method
        self.url = "http://example.com"
        self.query = {}
        self.headers = {}
        self.body = {}
        self.cookies = {}
        self.route_params = {}
        self.source = "flask"
        self.route = route
        self.parsed_userinput = {}


def get_test_context(ip, path="/", method="GET"):
    return Context(path, method, ip)


def new_attack_wave_detector():
    return AttackWaveDetector(
        attack_wave_threshold=6,
        attack_wave_time_frame=60 * 1000,
        min_time_between_events=60 * 60 * 1000,
        max_lru_entries=10_000,
    )


# Mock for get_unixtime_ms
def mock_get_unixtime_ms(monotonic=True, mock_time=0):
    return mock_time


def test_no_ip_address():
    detector = new_attack_wave_detector()
    assert not detector.check(get_test_context(None, "/wp-config.php", "GET"))


def test_not_a_web_scanner():
    detector = new_attack_wave_detector()
    assert not detector.check(get_test_context("::1", "/", "OPTIONS"))
    assert not detector.check(get_test_context("::1", "/", "GET"))
    assert not detector.check(get_test_context("::1", "/login", "GET"))
    assert not detector.check(get_test_context("::1", "/dashboard", "GET"))
    assert not detector.check(get_test_context("::1", "/dashboard/2", "GET"))
    assert not detector.check(get_test_context("::1", "/settings", "GET"))
    assert not detector.check(get_test_context("::1", "/", "GET"))
    assert not detector.check(get_test_context("::1", "/dashboard", "GET"))


def test_a_web_scanner():
    detector = new_attack_wave_detector()
    assert not detector.check(get_test_context("::1", "/wp-config.php", "GET"))
    assert not detector.check(get_test_context("::1", "/wp-config.php.bak", "GET"))
    assert not detector.check(get_test_context("::1", "/.git/config", "GET"))
    assert not detector.check(get_test_context("::1", "/.env", "GET"))
    assert not detector.check(get_test_context("::1", "/.htaccess", "GET"))
    # Is true because the threshold is 6
    assert detector.check(get_test_context("::1", "/.htpasswd", "GET"))
    # False again because event should have been sent last time
    assert not detector.check(get_test_context("::1", "/.htpasswd", "GET"))


def test_a_web_scanner_with_delays():
    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=0),
    ):
        detector = new_attack_wave_detector()
        assert not detector.check(get_test_context("::1", "/wp-config.php", "GET"))
        assert not detector.check(get_test_context("::1", "/wp-config.php.bak", "GET"))
        assert not detector.check(get_test_context("::1", "/.git/config", "GET"))
        assert not detector.check(get_test_context("::1", "/.env", "GET"))

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=30 * 1000),
    ):
        assert not detector.check(get_test_context("::1", "/.htaccess", "GET"))
        # Is true because the threshold is 6
        assert detector.check(get_test_context("::1", "/.htpasswd", "GET"))
        # False again because event should have been sent last time
        assert not detector.check(get_test_context("::1", "/.htpasswd", "GET"))

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=60 * 60 * 1000),
    ):
        # Still false because minimum time between events is 1 hour
        assert not detector.check(get_test_context("::1", "/.env", "GET"))
        assert not detector.check(get_test_context("::1", "/wp-config.php", "GET"))
        assert not detector.check(get_test_context("::1", "/wp-config.php.bak", "GET"))
        assert not detector.check(get_test_context("::1", "/.git/config", "GET"))
        assert not detector.check(get_test_context("::1", "/.env", "GET"))
        assert not detector.check(get_test_context("::1", "/.htaccess", "GET"))

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=92 * 60 * 1000),
    ):
        # Should resend event after 1 hour
        assert not detector.check(get_test_context("::1", "/.env", "GET"))
        assert not detector.check(get_test_context("::1", "/wp-config.php", "GET"))
        assert not detector.check(get_test_context("::1", "/wp-config.php.bak", "GET"))
        assert not detector.check(get_test_context("::1", "/.git/config", "GET"))
        assert not detector.check(get_test_context("::1", "/.env", "GET"))
        assert detector.check(get_test_context("::1", "/.htaccess", "GET"))


def test_a_slow_web_scanner_that_triggers_in_the_second_interval():
    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=0),
    ):
        detector = new_attack_wave_detector()
        assert not detector.check(get_test_context("::1", "/wp-config.php", "GET"))
        assert not detector.check(get_test_context("::1", "/wp-config.php.bak", "GET"))
        assert not detector.check(get_test_context("::1", "/.git/config", "GET"))
        assert not detector.check(get_test_context("::1", "/.env", "GET"))

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=62 * 1000),
    ):
        assert not detector.check(get_test_context("::1", "/.env", "GET"))
        assert not detector.check(get_test_context("::1", "/wp-config.php", "GET"))
        assert not detector.check(get_test_context("::1", "/wp-config.php.bak", "GET"))
        assert not detector.check(get_test_context("::1", "/.git/config", "GET"))
        assert not detector.check(get_test_context("::1", "/.env", "GET"))
        assert detector.check(get_test_context("::1", "/.htaccess", "GET"))


def test_a_slow_web_scanner_that_triggers_in_the_third_interval():
    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=0),
    ):
        detector = new_attack_wave_detector()
        assert not detector.check(get_test_context("::1", "/wp-config.php", "GET"))
        assert not detector.check(get_test_context("::1", "/wp-config.php.bak", "GET"))
        assert not detector.check(get_test_context("::1", "/.git/config", "GET"))
        assert not detector.check(get_test_context("::1", "/.env", "GET"))

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=62 * 1000),
    ):
        # Still false because minimum time between events is 1 hour
        assert not detector.check(get_test_context("::1", "/.env", "GET"))
        assert not detector.check(get_test_context("::1", "/wp-config.php", "GET"))
        assert not detector.check(get_test_context("::1", "/wp-config.php.bak", "GET"))
        assert not detector.check(get_test_context("::1", "/.git/config", "GET"))

    with patch(
        "aikido_zen.helpers.get_current_unixtime_ms.get_unixtime_ms",
        side_effect=lambda **kw: mock_get_unixtime_ms(**kw, mock_time=124 * 1000),
    ):
        # Should resend event after 1 hour
        assert not detector.check(get_test_context("::1", "/.env", "GET"))
        assert not detector.check(get_test_context("::1", "/wp-config.php", "GET"))
        assert not detector.check(get_test_context("::1", "/wp-config.php.bak", "GET"))
        assert not detector.check(get_test_context("::1", "/.git/config", "GET"))
        assert not detector.check(get_test_context("::1", "/.env", "GET"))
        assert detector.check(get_test_context("::1", "/.htaccess", "GET"))
