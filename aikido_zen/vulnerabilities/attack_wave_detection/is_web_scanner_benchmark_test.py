import time

import pytest

from aikido_zen.vulnerabilities.attack_wave_detection.is_web_scanner import (
    is_web_scanner,
)


class Context:
    def __init__(self, route, method, query):
        self.remote_address = "::1"
        self.method = method
        self.url = "http://example.com"
        self.query = query
        self.headers = {}
        self.body = {}
        self.cookies = {}
        self.route_params = {}
        self.source = "flask"
        self.route = route
        self.parsed_userinput = {}


def get_test_context(path="/", method="GET", query=None):
    return Context(path, method, query)


# the CI/CD results here are very unreliable, locally this test passes consistently.
@pytest.mark.skip(reason="Skipping this test in CI/CD")
def test_performance():
    iterations = 25_000
    start = time.perf_counter_ns()
    for _ in range(iterations):
        is_web_scanner(get_test_context("/wp-config.php", "GET", {"test": "1"}))
        is_web_scanner(
            get_test_context("/vulnerable", "GET", {"test": "1'; DROP TABLE users; --"})
        )
        is_web_scanner(get_test_context("/", "GET", {"test": "1"}))
    end = time.perf_counter_ns()

    total_time_ms = (end - start) / 1_000_000
    time_per_check_ms = total_time_ms / iterations / 3
    assert (
        time_per_check_ms < 0.006
    ), f"Took {time_per_check_ms:.6f}ms per check (max allowed: 0.006ms)"
